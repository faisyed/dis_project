# Performance Analysis of ARQ Protocols over Different Topologies
This repository contains the source code that is used to provide a thorough performance analysis of ARQ protocols across various network topologies. ARQ protocols boost data transmission reliability by applying error detection and correction techniques. However, their effectiveness depends on network topology due to latency, bandwidth, and congestion. A systematic experimental methodology uses network simulation tools to assess performance parameters like throughput and bit error rate. The findings show the strengths and drawbacks of several ARQ protocols in various network topologies, guiding protocol selection depending on the network's settings. The project focuses on the effect of network topology on ARQ protocol performance, providing insights into optimising selection and configuration. Ultimately, this work would improve data transmission reliability as well as effectiveness by aiding network designers and practitioners in selecting the most effective ARQ protocol for specific network topologies.

# Setup
This project requires setting a vitual environment to run the performance analysis evaluations. Follow the below steps to setup the environment and run the source code:
1. <b> Setting up a Linux environment using VirtualBox:</b> First step would be to setup a linux environment. Please follow the links for <a href=https://www.imore.com/how-use-linux-your-mac-using-virtual-machine>Mac Os</a> and <a href=https://www.c-sharpcorner.com/article/how-to-install-ubuntu-on-windows-10-using-virtualbox/>Windows</a>.
<br>
2. <b> Setting up following configuration for your virtual box:</b> Second step would be to set the following key configuration when setting up virtual box:
<ul>
    <li>Base Memory: 5145 MB
    <li>Processors: 4
    <li>Execution Cap: 100%
</ul>
3. Cloning this git repository in the linux enviroment
<br>
4. Ensure that python is installed in the environment if not install it.
<br>
5. Open terminal in the cloned git folder.
<br>
6. Run the following command to install requirements: pip install -r requirements.txt
<br>
7. Run the respective gbn or sr files by changing to respective directory and type python gbn_reed.py or python sr_reed.py

# Note
All the files in this repository are set to the base value of evaluation metrics. To obtain the results we carried out the tests by changing the values at runtime.

