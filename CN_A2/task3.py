"""CS3001 Assignment-II - Task 3: GBN & SR implementation over a simulated unreliable channel.
  Muhammad Hammad 24k-0544
"""
import argparse
import heapq
import random
from collections import defaultdict
from dataclasses import dataclass

DATA_BITS, ACK_BITS, L_BITS = 8000, 320, 8000
DATA, ACK = "DATA", "ACK"


def make_checksum(kind, seq, data):
    raw = bytes([1 if kind == DATA else 2]) + seq.to_bytes(2, "big") + data
    if len(raw) % 2:
        raw += b"\x00"
    total = 0
    for i in range(0, len(raw), 2):
        total += (raw[i] << 8) + raw[i + 1]
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


@dataclass
class Packet:
    kind: str
    seq: int              # wire sequence number = absolute number % 2^k
    data: bytes = b""
    checksum: int = 0
    idx: int = -1         # debug only (absolute index) - protocols never read it

    @staticmethod
    def make(kind, seq, data=b"", idx=-1):
        return Packet(kind, seq, data, make_checksum(kind, seq, data), idx)

    def __str__(self):
        return f"{self.kind} {self.seq}"


def is_corrupt(p):
    return p.checksum != make_checksum(p.kind, p.seq, p.data)


def corrupt_copy(p, rng):
    q = Packet(p.kind, p.seq, p.data, p.checksum, p.idx)
    if q.data:
        b = bytearray(q.data)
        b[rng.randrange(len(b))] ^= 1 << rng.randrange(8)
        q.data = bytes(b)
    else:
        q.seq ^= 1 << rng.randrange(4)
    return q



class Simulator:
    def __init__(self, verbose=True):
        self.now = 0.0
        self._q, self._n, self._cancelled = [], 0, set()
        self.stopped = False
        self.verbose = verbose

    def schedule(self, delay, fn, *args):
        self._n += 1
        heapq.heappush(self._q, (self.now + delay, self._n, fn, args))
        return self._n                      # event id, used to cancel a timer

    def cancel(self, event_id):
        if event_id is not None:
            self._cancelled.add(event_id)

    def log(self, msg):
        if self.verbose:
            print(f"[t={self.now:8.3f}] {msg}")

    def run(self, max_time):
        while self._q and not self.stopped:
            t, eid, fn, args = heapq.heappop(self._q)
            if eid in self._cancelled:
                continue
            if t > max_time:
                return False                # gave up (e.g. deadlock with unsafe window)
            self.now = t
            fn(*args)
        return self.stopped



class Channel:
    def __init__(self, sim, name, deliver, rng, stats, loss=0.0, corrupt=0.0, delay=0.0,
                 delay_max=0.2, rate=2_000_000, prop=0.25, drop_first=()):
        self.sim, self.name, self.deliver, self.rng, self.stats = sim, name, deliver, rng, stats
        self.loss, self.corrupt, self.delay, self.delay_max = loss, corrupt, delay, delay_max
        self.rate, self.prop = rate, prop
        self.free_at = 0.0                  # when the transmitter is next idle
        self.drop_first = set(drop_first)   # scripted: drop 1st transmission of these DATA indices

    def send(self, pkt, bits):
        s = self.sim
        depart = max(s.now, self.free_at) + bits / self.rate     # L/R transmission time
        self.free_at = depart
        kind = "pkt" if pkt.kind == DATA else "ACK"
        if pkt.kind == DATA and pkt.idx in self.drop_first:
            self.drop_first.discard(pkt.idx)
            lost = True
        else:
            lost = self.rng.random() < self.loss
        if lost:
            self.stats[f"lost_{pkt.kind}"] += 1
            s.log(f"  ** {kind} {pkt.seq} LOST in channel")
            return
        if self.rng.random() < self.corrupt:
            pkt = corrupt_copy(pkt, self.rng)
            self.stats[f"corrupted_{pkt.kind}"] += 1
            s.log(f"  ** {kind} {pkt.seq} CORRUPTED in channel")
        extra = 0.0
        if self.rng.random() < self.delay:
            extra = self.rng.uniform(0.05, self.delay_max)
            self.stats["delayed"] += 1
            s.log(f"  ** {kind} {pkt.seq} DELAYED by {extra:.3f}s")
        s.schedule(depart + self.prop + extra - s.now, self.deliver, pkt)



class GBNSender:
    def __init__(self, sim, chan, payloads, N, M, timeout, stats, on_done):
        self.sim, self.chan, self.payloads = sim, chan, payloads
        self.N, self.M, self.timeout, self.stats, self.on_done = N, M, timeout, stats, on_done
        self.base = 0                # oldest unACKed packet
        self.nextseqnum = 0          # next packet to send
        self.timer = None            # ONE timer, for the oldest unACKed packet (base)
        self.sent_once = set()

    def start(self):
        self.try_send()

    def transmit(self, i):
        retx = i in self.sent_once
        self.sent_once.add(i)
        self.stats["data_sent"] += 1
        self.stats["retransmissions"] += retx
        self.sim.log(f"{'RETRANSMIT' if retx else 'SEND'} pkt {i % self.M} (#{i})  "
                     f"window=[{self.base}-{self.base + self.N - 1}]")
        self.chan.send(Packet.make(DATA, i % self.M, self.payloads[i], idx=i), DATA_BITS)

    def start_timer(self):
        self.sim.cancel(self.timer)
        self.timer = self.sim.schedule(self.timeout, self.on_timeout)

    def try_send(self):
        while self.nextseqnum < self.base + self.N and self.nextseqnum < len(self.payloads):
            self.transmit(self.nextseqnum)
            if self.base == self.nextseqnum:
                self.start_timer()
            self.nextseqnum += 1

    def on_ack(self, p):
        if is_corrupt(p):
            self.sim.log("  sender: corrupted ACK ignored")
            return
        off = (p.seq - self.base) % self.M              # distance from base in modulo space
        if off < self.nextseqnum - self.base:           # cumulative ACK for new data
            self.base += off + 1
            self.sim.log(f"  sender: ACK {p.seq} (cumulative) -> base={self.base}")
            if self.base == len(self.payloads):
                self.sim.cancel(self.timer)
                self.sim.stopped = True
                self.on_done()
                return
            if self.base == self.nextseqnum:
                self.sim.cancel(self.timer); self.timer = None
            else:
                self.start_timer()
            self.try_send()
        else:
            self.sim.log(f"  sender: duplicate ACK {p.seq} ignored (base={self.base})")

    def on_timeout(self):
        self.stats["timeouts"] += 1
        self.sim.log(f"TIMEOUT (oldest unACKed pkt {self.base % self.M}) -> go back, "
                     f"resend {self.base}..{self.nextseqnum - 1}")
        self.start_timer()
        for i in range(self.base, self.nextseqnum):
            self.transmit(i)


class GBNReceiver:
    def __init__(self, sim, chan, M, stats):
        self.sim, self.chan, self.M, self.stats = sim, chan, M, stats
        self.expectedseqnum = 0
        self.delivered = []

    def send_ack(self, n):
        self.stats["acks_sent"] += 1
        self.chan.send(Packet.make(ACK, n % self.M), ACK_BITS)

    def on_packet(self, p):
        if is_corrupt(p):
            self.sim.log("  receiver: corrupted packet discarded -> re-ACK last in-order")
        elif p.seq == self.expectedseqnum % self.M:
            self.delivered.append(p.data)
            self.sim.log(f"  receiver: pkt {p.seq} in order, DELIVER, ACK {p.seq}")
            self.send_ack(self.expectedseqnum)
            self.expectedseqnum += 1
            return
        else:
            self.sim.log(f"  receiver: pkt {p.seq} out of order (expected "
                         f"{self.expectedseqnum % self.M}) DISCARD -> re-ACK")
        if self.expectedseqnum > 0:
            self.send_ack(self.expectedseqnum - 1)      # cumulative ACK of last in-order


class SRSender:
    def __init__(self, sim, chan, payloads, N, M, timeout, stats, on_done):
        self.sim, self.chan, self.payloads = sim, chan, payloads
        self.N, self.M, self.timeout, self.stats, self.on_done = N, M, timeout, stats, on_done
        self.base = 0
        self.nextseqnum = 0
        self.acked = set()           # per-packet "acked" flag
        self.timers = {}             # per-packet timer
        self.sent_once = set()

    def start(self):
        self.try_send()

    def transmit(self, i):
        retx = i in self.sent_once
        self.sent_once.add(i)
        self.stats["data_sent"] += 1
        self.stats["retransmissions"] += retx
        self.sim.log(f"{'RETRANSMIT' if retx else 'SEND'} pkt {i % self.M} (#{i})  "
                     f"window=[{self.base}-{self.base + self.N - 1}]")
        self.chan.send(Packet.make(DATA, i % self.M, self.payloads[i], idx=i), DATA_BITS)
        self.sim.cancel(self.timers.get(i))
        self.timers[i] = self.sim.schedule(self.timeout, self.on_timeout, i)   # own timer

    def try_send(self):
        while self.nextseqnum < self.base + self.N and self.nextseqnum < len(self.payloads):
            self.transmit(self.nextseqnum)
            self.nextseqnum += 1

    def on_ack(self, p):
        if is_corrupt(p):
            self.sim.log("  sender: corrupted ACK ignored")
            return
        off = (p.seq - self.base) % self.M
        if off >= self.nextseqnum - self.base:
            self.sim.log(f"  sender: stale ACK {p.seq} ignored")
            return
        i = self.base + off
        if i not in self.acked:
            self.acked.add(i)
            self.sim.cancel(self.timers.pop(i, None))
            self.sim.log(f"  sender: ACK {p.seq} (individual) -> pkt #{i} marked acked")
        while self.base in self.acked:                  # slide window past contiguous acked
            self.acked.discard(self.base)
            self.base += 1
        if self.base == len(self.payloads):
            self.sim.stopped = True
            self.on_done()
            return
        self.try_send()

    def on_timeout(self, i):
        if i in self.acked or i < self.base:
            return
        self.stats["timeouts"] += 1
        self.sim.log(f"TIMEOUT pkt {i % self.M} (#{i}) -> resend only this packet")
        self.transmit(i)


class SRReceiver:
    def __init__(self, sim, chan, N, M, stats):
        self.sim, self.chan, self.N, self.M, self.stats = sim, chan, N, M, stats
        self.rcv_base = 0
        self.buffer = {}
        self.delivered = []

    def send_ack(self, seq):
        self.stats["acks_sent"] += 1
        self.chan.send(Packet.make(ACK, seq), ACK_BITS)

    def on_packet(self, p):
        if is_corrupt(p):
            self.sim.log("  receiver: corrupted packet ignored")
            return
        off = (p.seq - self.rcv_base) % self.M
        if off < self.N:                                # inside receive window
            i = self.rcv_base + off
            if i not in self.buffer:
                self.buffer[i] = p.data
            self.sim.log(f"  receiver: pkt {p.seq} in window -> buffer, ACK {p.seq}")
            self.send_ack(p.seq)
            while self.rcv_base in self.buffer:         # deliver in order
                self.delivered.append(self.buffer.pop(self.rcv_base))
                self.sim.log(f"  receiver: DELIVER #{self.rcv_base}")
                self.rcv_base += 1
        elif off >= self.M - self.N:                    # previous window: ACK was lost
            self.sim.log(f"  receiver: old pkt {p.seq} (already delivered) -> re-ACK")
            self.send_ack(p.seq)
        else:
            self.sim.log(f"  receiver: pkt {p.seq} outside windows, ignored")



def run(protocol="gbn", packets=200, window=4, k=3, loss=0.0, corrupt=0.0, delay=0.0,
        delay_max=0.2, timeout=1.0, seed=544, verbose=False, drop_first=(),
        allow_unsafe=False, rate=2_000_000, rtt=0.5):
    M = 2 ** k
    limit = M - 1 if protocol == "gbn" else M // 2
    if window > limit and not allow_unsafe:
        raise SystemExit(f"window {window} too big for {protocol.upper()} with k={k} "
                         f"(max {limit}). Use --allow-unsafe to see the ambiguity bug.")
    rng = random.Random(seed)
    sim = Simulator(verbose)
    stats = defaultdict(int)
    payloads = [f"casualty-list-{i}".encode() for i in range(packets)]
    holder = {}
    to_rx = lambda p: holder["rx"].on_packet(p)
    to_tx = lambda p: holder["tx"].on_ack(p)
    opts = dict(loss=loss, corrupt=corrupt, delay=delay, delay_max=delay_max, rate=rate,
                prop=rtt / 2)
    fwd = Channel(sim, "fwd", to_rx, rng, stats, drop_first=drop_first, **opts)
    rev = Channel(sim, "rev", to_tx, rng, stats, **opts)
    if protocol == "gbn":
        holder["tx"] = GBNSender(sim, fwd, payloads, window, M, timeout, stats, lambda: None)
        holder["rx"] = GBNReceiver(sim, rev, M, stats)
    else:
        holder["tx"] = SRSender(sim, fwd, payloads, window, M, timeout, stats, lambda: None)
        holder["rx"] = SRReceiver(sim, rev, window, M, stats)
    holder["tx"].start()
    finished = sim.run(max_time=200 + packets * 10)
    got = holder["rx"].delivered
    elapsed = sim.now
    return dict(protocol=protocol.upper(), transmitted=stats["data_sent"],
                retransmissions=stats["retransmissions"], delivered=len(got),
                correct=(finished and got == payloads), finished=finished,
                time_s=elapsed, throughput_kbps=len(got) * L_BITS / elapsed / 1000 if elapsed else 0,
                timeouts=stats["timeouts"], acks_sent=stats["acks_sent"],
                lost_data=stats["lost_DATA"], lost_acks=stats["lost_ACK"],
                corrupted=stats["corrupted_DATA"] + stats["corrupted_ACK"],
                delayed=stats["delayed"])


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    a.add_argument("--protocol", choices=["gbn", "sr"], required=True)
    a.add_argument("--packets", type=int, default=20)
    a.add_argument("--window", type=int, default=4, help="window size N")
    a.add_argument("--k", type=int, default=3, help="sequence-number bits (numbers wrap mod 2^k)")
    a.add_argument("--loss", type=float, default=0.0)
    a.add_argument("--corrupt", type=float, default=0.0)
    a.add_argument("--delay", type=float, default=0.0, help="probability of extra delay")
    a.add_argument("--delay-max", type=float, default=0.2, help="max extra delay (s)")
    a.add_argument("--timeout", type=float, default=1.0, help="retransmission timeout (s); keep > max RTT (~0.95 s)")
    a.add_argument("--seed", type=int, default=544, help="last 4 digits of roll number")
    a.add_argument("--drop-first", type=int, nargs="*", default=[],
                   help="scripted: drop first transmission of these packet indices (Task 2)")
    a.add_argument("--allow-unsafe", action="store_true", help="allow window beyond safe limit")
    a.add_argument("--quiet", action="store_true", help="no per-event log")
    x = a.parse_args()
    r = run(x.protocol, x.packets, x.window, x.k, x.loss, x.corrupt, x.delay, x.delay_max,
            x.timeout, x.seed, not x.quiet, x.drop_first, x.allow_unsafe)
    print("\n=== SUMMARY ===")
    for key, v in r.items():
        print(f"{key:16}: {v:.3f}" if isinstance(v, float) else f"{key:16}: {v}")


if __name__ == "__main__":
    main()