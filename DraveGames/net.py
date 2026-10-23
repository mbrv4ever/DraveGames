# -*- coding: utf-8 -*-
"""net.py - eenvoudige LAN-multiplayer voor DraveGames (beurt-om-beurt).

Ontwerp:
  * Protocol = regelgebaseerde JSON over TCP (elk bericht is een dict + '\\n').
  * Host = speler 1, client = speler 2.
  * Discovery via UDP-broadcast, zodat een client een host op het LAN
    automatisch kan vinden (naast handmatig IP intypen).
  * Alles draait in achtergrond-threads; de game leest binnenkomende
    berichten op met poll() (niet-blokkerend, veilig vanuit de game-loop).

Dit bestand heeft GEEN pygame nodig en kan los getest worden:
    python -c "import net; print(net.local_ip())"
"""
from __future__ import annotations

import json
import socket
import threading
import time

TCP_PORT = 50777          # spelpoort (TCP)
DISCOVERY_PORT = 50778    # discovery (UDP)
MAGIC = "DRAVEGAMES_LAN"  # herkenning bij discovery


def local_ip() -> str:
    """Beste gok voor het LAN-IP van deze pc (zonder echt te verzenden)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class NetPeer:
    """Eén netwerkverbinding (host of client).

    Gebruik:
        peer = NetPeer()
        peer.host()                 # of: peer.join("192.168.1.23")
        ... in de game-loop ...
        if peer.connected: ...
        for msg in peer.poll(): ... # binnengekomen dicts
        peer.send({"type": "...", ...})
        peer.close()
    """

    def __init__(self):
        self.conn = None
        self.is_host = False
        self.connected = False
        self.error = None
        self.peer_ip = None
        self._inbox = []
        self._lock = threading.Lock()
        self._stop = False
        self._buf = b""

    # ------------------------------------------------------------------ host
    def host(self):
        """Start een server-thread + een discovery-responder."""
        self.is_host = True
        self.error = None
        threading.Thread(target=self._host_thread, daemon=True).start()
        threading.Thread(target=self._discovery_responder, daemon=True).start()

    def _host_thread(self):
        srv = None
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(("", TCP_PORT))
            srv.listen(1)
            srv.settimeout(0.5)
            while not self._stop and self.conn is None:
                try:
                    conn, addr = srv.accept()
                except socket.timeout:
                    continue
                self.conn = conn
                self.peer_ip = addr[0]
                self.connected = True
                self._recv_loop(conn)
                break
        except Exception as e:
            self.error = str(e)
        finally:
            try:
                if srv:
                    srv.close()
            except Exception:
                pass

    def _discovery_responder(self):
        """Antwoord op broadcast-zoekberichten zolang we nog niet verbonden zijn."""
        us = None
        try:
            us = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            us.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            us.bind(("", DISCOVERY_PORT))
            us.settimeout(0.5)
            while not self._stop and not self.connected:
                try:
                    data, addr = us.recvfrom(1024)
                except socket.timeout:
                    continue
                if data.decode("utf-8", "ignore").strip() == MAGIC + "?":
                    try:
                        us.sendto((MAGIC + "!").encode("utf-8"), addr)
                    except Exception:
                        pass
        except Exception:
            pass
        finally:
            try:
                if us:
                    us.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ join
    def join(self, ip: str):
        """Verbind als client met een host op het opgegeven IP."""
        self.is_host = False
        self.error = None
        threading.Thread(target=self._join_thread, args=(ip,), daemon=True).start()

    def _join_thread(self, ip: str):
        try:
            c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            c.settimeout(5.0)
            c.connect((ip, TCP_PORT))
            c.settimeout(None)
            self.conn = c
            self.peer_ip = ip
            self.connected = True
            self._recv_loop(c)
        except Exception as e:
            self.error = str(e)
            self.connected = False

    @staticmethod
    def discover(timeout: float = 2.5):
        """Zoek hosts op het LAN. Stuurt herhaald naar zowel het globale als het
        subnet-broadcast-adres (belangrijk op Windows met meerdere adapters)."""
        found = []
        # doel-broadcastadressen bepalen
        targets = ["255.255.255.255"]
        try:
            ip = local_ip()
            if ip and ip.count(".") == 3 and not ip.startswith("127."):
                targets.append(ip.rsplit(".", 1)[0] + ".255")   # bijv. 192.168.1.255
        except Exception:
            pass
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.settimeout(0.3)
            t0 = time.time()
            last_send = -1.0
            msg = (MAGIC + "?").encode("utf-8")
            while time.time() - t0 < timeout:
                # elke ~0.5 s opnieuw uitzenden naar alle doelen
                if time.time() - last_send > 0.5:
                    for tgt in targets:
                        try:
                            s.sendto(msg, (tgt, DISCOVERY_PORT))
                        except Exception:
                            pass
                    last_send = time.time()
                try:
                    data, addr = s.recvfrom(1024)
                except socket.timeout:
                    continue
                except Exception:
                    break
                if data.decode("utf-8", "ignore").strip() == MAGIC + "!":
                    if addr[0] not in found:
                        found.append(addr[0])
        except Exception:
            pass
        finally:
            try:
                if s:
                    s.close()
            except Exception:
                pass
        return found

    # -------------------------------------------------------------------- io
    def _recv_loop(self, conn):
        try:
            while not self._stop:
                data = conn.recv(4096)
                if not data:
                    break
                self._buf += data
                while b"\n" in self._buf:
                    line, self._buf = self._buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line.decode("utf-8"))
                    except Exception:
                        continue
                    with self._lock:
                        self._inbox.append(msg)
        except Exception as e:
            self.error = str(e)
        self.connected = False

    def send(self, msg: dict):
        """Verstuur een dict als JSON-regel. Stil falen als er geen verbinding is."""
        if not self.conn:
            return
        try:
            self.conn.sendall((json.dumps(msg) + "\n").encode("utf-8"))
        except Exception as e:
            self.error = str(e)

    def poll(self):
        """Geef de tot nu toe binnengekomen berichten terug en leeg de inbox."""
        with self._lock:
            msgs = self._inbox
            self._inbox = []
        return msgs

    def close(self):
        self._stop = True
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.conn = None
        self.connected = False


# Snelle zelftest (geen echte verbinding): python net.py
if __name__ == "__main__":
    print("Lokaal IP:", local_ip())
    print("TCP-poort:", TCP_PORT, " discovery-poort:", DISCOVERY_PORT)
    print("Discovery (1.5s)...", NetPeer.discover())
