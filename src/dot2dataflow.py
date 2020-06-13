import argparse
import networkx as nx
from make_test_bench import make_test_bench

def main(dot_file,output_dir):
    
    dataflow_dot = nx.DiGraph(nx.nx_pydot.read_dot(dot_file))
    make_test_bench(dataflow_dot).to_verilog(output_dir +'/test_bench_'+dataflow_dot.name + '.v')
    

if __name__ == '__main__':    
    parser = argparse.ArgumentParser('python3 dot2dataflow')
    parser.add_argument('dot_dataflow', help='dot file')
    parser.add_argument('output_dir',default='.',help='output_dir: default .')
    args = parser.parse_args()
    
    try:
        main(args.dot_dataflow,args.output_dir)
    except Exception as e:
        print(e)
