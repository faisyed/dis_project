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

class SelectiveRepeatSender:
    def __init__(self, error_rate, frame_size, window_size, reedsolomon_n, reedsolomon_k):
        self.error_rate = error_rate
        self.frame_size = frame_size
        self.window_size = window_size
        self.crc_func = crcmod.predefined.mkCrcFun('crc-16')
        self.rs = RSCodec(reedsolomon_n - reedsolomon_k)

    def create_frame(self, seq_num):
        data = bytearray(random.getrandbits(8) for _ in range(self.frame_size))
        rs_encoded_data = self.rs.encode(data)
        crc = self.crc_func(rs_encoded_data)
        return Frame(seq_num, rs_encoded_data, crc)

    def is_faulty(self, frame):
        return random.random() < self.error_rate

class SelectiveRepeatReceiver:
    def __init__(self, error_rate, window_size, num_nodes, reedsolomon_n, reedsolomon_k):
        self.error_rate = error_rate
        self.window_size = window_size
        self.crc_func = crcmod.predefined.mkCrcFun('crc-16')
        self.expected_seq_num = [0] * num_nodes
        self.rs = RSCodec(reedsolomon_n - reedsolomon_k)
        self.received_frames = []
        for _ in range(num_nodes):
            self.received_frames.append(collections.deque(maxlen=window_size))

    def is_faulty(self, frame):
        return random.random() < self.error_rate

    def read_frame(self, frame, sender_id):
        if self.is_faulty(frame):
            return False, frame.seq_num

        try:
            decoded_data = self.rs.decode(frame.data)
        except ReedSolomonError:
            return False, frame.seq_num

        seq_num = frame.seq_num
        expected_seq_num = self.expected_seq_num[sender_id]

        if seq_num >= expected_seq_num and seq_num < expected_seq_num + self.window_size:
            self.received_frames[sender_id].append(frame)

            def function(f):
                return f.seq_num

            self.received_frames[sender_id] = collections.deque(sorted(self.received_frames[sender_id], key=function), maxlen=self.window_size)

            while self.received_frames[sender_id] and self.received_frames[sender_id][0].seq_num == expected_seq_num:
                self.expected_seq_num[sender_id] += 1
                expected_seq_num += 1
                self.received_frames[sender_id].popleft()

            return True, seq_num
        else:
            return False, seq_num


def run_simulation(senders, receiver, num_frames, timeout, num_rows, num_cols, center):
    num_nodes = (num_rows * num_cols)-1
    sent_frames = [0] * num_nodes
    acked_frames = [0] * num_nodes
    resend_count = [0] * num_nodes
    seq_num = [0] * num_nodes
    start_time = time.time()

    while min(acked_frames) < num_frames:
        for sender_id in range(num_nodes):
            if acked_frames[sender_id] >= num_frames:
                continue

            base_seq_num = seq_num[sender_id] - len(receiver.received_frames[sender_id])
            if seq_num[sender_id] < base_seq_num + senders[sender_id].window_size:
                frame = senders[sender_id].create_frame(seq_num[sender_id])
                sent_frames[sender_id] += 1

                if senders[sender_id].is_faulty(frame):
                    resend_count[sender_id] += 1
                    time.sleep(timeout)
                    continue

                ack, frame_seq_num = receiver.read_frame(frame, sender_id)
                if ack:
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
    num_rows = 5
    num_cols = 1
    frame_size = 600
    num_frames = 60
    error_rate = 0.05
    timeout = 1
    window_size = 100
    rs_n, rs_k = 255, 223

    # for number of columns
    metric_num_of_columns(error_rate, frame_size, num_frames, num_rows, rs_k, rs_n, timeout, window_size)
    
    num_cols = 1
    # for frame size
    metric_frame_size(error_rate, num_cols, num_frames, num_rows, rs_k, rs_n, timeout, window_size)

    frame_size = 600
    # number of frames
    metric_num_of_frames(error_rate, frame_size, num_cols, num_rows, rs_k, rs_n, timeout, window_size)
    
    num_frames = 60
    # for error rate
    metric_error_rate(frame_size, num_cols, num_frames, num_rows, rs_k, rs_n, timeout, window_size)


def metric_error_rate(frame_size, num_cols, num_frames, num_rows, rs_k, rs_n, timeout, window_size):
    for i in range(1, 6):
        error_rate = 0.05 * i
        print(f"Error rate: {error_rate}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.grid_2d_graph(num_rows, num_cols)
            center = nx.center(G)[0]
            receiver = SelectiveRepeatReceiver(error_rate, window_size, num_rows * num_cols, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for row in range(num_rows):
                for col in range(num_cols):
                    node = (row, col)
                    if node != center:
                        i = row * (num_cols - 1) + col
                        G.nodes[node]['obj'] = SelectiveRepeatSender(error_rate, frame_size, window_size, rs_n, rs_k)
                        senders.append(G.nodes[node]['obj'])

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_rows, num_cols, center)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


def metric_num_of_frames(error_rate, frame_size, num_cols, num_rows, rs_k, rs_n, timeout, window_size):
    for num_frames in range(60, 91, 10):
        print(f"Number of frames: {num_frames}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.grid_2d_graph(num_rows, num_cols)
            center = nx.center(G)[0]
            receiver = SelectiveRepeatReceiver(error_rate, window_size, num_rows * num_cols, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for row in range(num_rows):
                for col in range(num_cols):
                    node = (row, col)
                    if node != center:
                        i = row * (num_cols - 1) + col
                        G.nodes[node]['obj'] = SelectiveRepeatSender(error_rate, frame_size, window_size, rs_n, rs_k)
                        senders.append(G.nodes[node]['obj'])

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_rows, num_cols, center)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


def metric_frame_size(error_rate, num_cols, num_frames, num_rows, rs_k, rs_n, timeout, window_size):
    for frame_size in range(600, 1001, 100):
        print(f"Frame size: {frame_size}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.grid_2d_graph(num_rows, num_cols)
            center = nx.center(G)[0]
            receiver = SelectiveRepeatReceiver(error_rate, window_size, num_rows * num_cols, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for row in range(num_rows):
                for col in range(num_cols):
                    node = (row, col)
                    if node != center:
                        i = row * (num_cols - 1) + col
                        G.nodes[node]['obj'] = SelectiveRepeatSender(error_rate, frame_size, window_size, rs_n, rs_k)
                        senders.append(G.nodes[node]['obj'])

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_rows, num_cols, center)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


def metric_num_of_columns(error_rate, frame_size, num_frames, num_rows, rs_k, rs_n, timeout, window_size):
    for num_cols in range(1, 6):
        print(f"Number of columns: {num_cols}")
        tp_ar = []
        ber_ar = []
        for _ in range(25):
            G = nx.grid_2d_graph(num_rows, num_cols)
            center = nx.center(G)[0]
            receiver = SelectiveRepeatReceiver(error_rate, window_size, num_rows * num_cols, rs_n, rs_k)
            G.nodes[center]['obj'] = receiver
            senders = []
            for row in range(num_rows):
                for col in range(num_cols):
                    node = (row, col)
                    if node != center:
                        i = row * (num_cols - 1) + col
                        G.nodes[node]['obj'] = SelectiveRepeatSender(error_rate, frame_size, window_size, rs_n, rs_k)
                        senders.append(G.nodes[node]['obj'])

            throughput, ber = run_simulation(senders, receiver, num_frames, timeout, num_rows, num_cols, center)
            tp_ar.append(throughput)
            ber_ar.append(ber)
        print(f"Throughput: {sum(tp_ar) / len(tp_ar)} frames/sec")
        print(f"Bit Error Rate: {sum(ber_ar) / len(ber_ar)}")


if __name__ == "__main__":
    main()
            
