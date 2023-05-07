import time
import random
import collections
import networkx as nx
import crcmod
from reedsolo import RSCodec, ReedSolomonError


class Frame:
    def __init__(self, sequence_number, data, crc):
        self.seq_num = sequence_number
        self.data = data
        self.crc = crc


class GoBackNSender:
    def __init__(self, error_rate, frame_size, reedSolomon_n, reedSolomon_k):
        self.error_rate = error_rate
        self.frame_size = frame_size
        self.crc_function = crcmod.predefined.mkCrcFun('crc-16')
        self.reedSolomon = RSCodec(reedSolomon_n - reedSolomon_k)

    def create_frame(self, sequence_number):
        data = bytearray(random.getrandbits(8) for _ in range(self.frame_size))
        reedSolomon_encoded_data = self.reedSolomon.encode(data)
        crc = self.crc_function(reedSolomon_encoded_data)
        return Frame(sequence_number, reedSolomon_encoded_data, crc)

    def is_faulty(self, frame):
        return self.error_rate > random.random()


class GoBackNReceiver:
    def __init__(self, error_rate, num_nodes, reedSolomon_n, reedSolomon_k):
        self.error_rate = error_rate
        self.crc_func = crcmod.predefined.mkCrcFun('crc-16')
        self.expected_seq_num = [0] * num_nodes
        self.rs = RSCodec(reedSolomon_n - reedSolomon_k)

    def is_faulty(self, frame):
        return self.error_rate > random.random()

    def read_frame(self, frame, sender_id):
        if self.is_faulty(frame) or frame.seq_num != self.expected_seq_num[sender_id]:
            return False

        try:
            decoded_data = self.rs.decode(frame.data)
        except ReedSolomonError:
            return False

        self.expected_seq_num[sender_id] += 1
        return True

def run_simulation(senders, receiver, num_frames, timeout, num_nodes):
    sent_frames = [0] * num_nodes
    acked_frames = [0] * num_nodes
    resend_count = [0] * num_nodes
    seq_num = [0] * num_nodes
    start_time = time.time()

    while min(acked_frames) < num_frames:
        for sender_id in range(num_nodes):
            if acked_frames[sender_id] >= num_frames:
                continue

            frame = senders[sender_id].create_frame(seq_num[sender_id])
            sent_frames[sender_id] += 1

            if senders[sender_id].is_faulty(frame):
                resend_count[sender_id] += 1
                time.sleep(timeout)
                continue

            if receiver.read_frame(frame, sender_id):
                acked_frames[sender_id] += 1
                seq_num[sender_id] += 1

    elapsed_time = time.time() - start_time
    total_sent_frames = sum(sent_frames)
    total_resend_count = sum(resend_count)
    total_acked_frames = sum(acked_frames)

    throughput = total_acked_frames / elapsed_time
    ber = total_resend_count / total_sent_frames

    return throughput, ber

def main():
    num_nodes = 5
    frame_size = 600
    num_frames = 60
    error_rate = 0.05
    timeout = 1
    rs_n, rs_k = 255, 223

    # for number of nodes
    metric_num_of_nodes(error_rate, frame_size, num_frames, rs_k, rs_n, timeout)
    
    num_nodes = 5
    # for frame size
    metric_frame_size(error_rate, num_frames, num_nodes, rs_k, rs_n, timeout)
    
    frame_size = 600
    # for number of frames
    metric_num_of_frames(error_rate, frame_size, num_nodes, rs_k, rs_n, timeout)
    
    num_frames = 60
    # for error rate
    metric_error_rate(frame_size, num_frames, num_nodes, rs_k, rs_n, timeout)


def metric_error_rate(frame_size, num_frames, num_nodes, rs_k, rs_n, timeout):
    for i in range(1, 6):
        error_rate = 0.05 * i
        print(f"Error rate: {error_rate}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.complete_graph(num_nodes)
            center = nx.center(G)[0]
            receiver = GoBackNReceiver(error_rate, num_nodes, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for i in range(0, num_nodes):
                senders.append(GoBackNSender(error_rate, frame_size, rs_n, rs_k))
            for i, sender in enumerate(senders):
                if i != center:
                    G.nodes[i]['obj'] = sender

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_nodes)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


def metric_num_of_frames(error_rate, frame_size, num_nodes, rs_k, rs_n, timeout):
    for num_frames in range(60, 91, 10):
        print(f"Number of frames: {num_frames}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.complete_graph(num_nodes)
            center = nx.center(G)[0]
            receiver = GoBackNReceiver(error_rate, num_nodes, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for i in range(0, num_nodes):
                senders.append(GoBackNSender(error_rate, frame_size, rs_n, rs_k))
            for i, sender in enumerate(senders):
                if i != center:
                    G.nodes[i]['obj'] = sender

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_nodes)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


def metric_frame_size(error_rate, num_frames, num_nodes, rs_k, rs_n, timeout):
    for frame_size in range(600, 1001, 100):
        print(f"Frame size: {frame_size}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.complete_graph(num_nodes)
            center = nx.center(G)[0]
            receiver = GoBackNReceiver(error_rate, num_nodes, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for i in range(0, num_nodes):
                senders.append(GoBackNSender(error_rate, frame_size, rs_n, rs_k))
            for i, sender in enumerate(senders):
                if i != center:
                    G.nodes[i]['obj'] = sender

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_nodes)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


def metric_num_of_nodes(error_rate, frame_size, num_frames, rs_k, rs_n, timeout):
    for num_nodes in range(5, 26, 5):
        print(f"Number of nodes: {num_nodes}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.complete_graph(num_nodes)
            center = nx.center(G)[0]
            receiver = GoBackNReceiver(error_rate, num_nodes, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for i in range(0, num_nodes):
                senders.append(GoBackNSender(error_rate, frame_size, rs_n, rs_k))
            for i, sender in enumerate(senders):
                if i != center:
                    G.nodes[i]['obj'] = sender

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_nodes)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


if __name__ == "__main__":
    main()
