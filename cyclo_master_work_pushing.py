import argparse
import os
from git import Repo
import requests
import numpy as np
from threading import Timer
from flask import Flask,json,request,jsonify
import timeit
from multiprocessing import Process

app = Flask(__name__)



def call_back():
    print "Total Cyclometric Complexity calculated ----------> ",np.sum(cc_manager.total)
    elapsed = timeit.default_timer() - start_time
    print " ELAPSED TIME ------------------->", elapsed

@app.route('/', methods=['POST'])
def post():

    if request.headers['CONTENT_TYPE'] == 'application/json':
        data = json.loads(json.dumps(request.json))
        print("Total Cyclometric Complexity calculated by worker ", data['worker_id'], " is -----> ",
              data['total_cyclometric_complexity'])
        cc_manager.total.append(int(data['total_cyclometric_complexity']))

    t = Timer(5.0, call_back)
    t.start()
    return "success"




class CodeComplexityMaster:

    def __init__(self ,slave_ip, slave_port , master_port):

        if  slave_ip and  slave_port:
            self.slave_address = "http://{0}:{1}".format(slave_ip, slave_port)
            self.slave_address_seond = "http://{0}:{1}".format(slave_ip, slave_port+1)
            self.master_address = "http://{0}:{1}".format(slave_ip, master_port)
            print self.master_address


        print("Initialising Master...")

        # GIT repository settings
        self.git_repository = "https://github.com/DLTK/DLTK"
        self.root_repo_dir = "./repo"
        self.commits = []
        self.total = []
        self.cc_per_commit = {}
        self.repo = None

    def setup_gitrepo(self):

        repo_dir = self.root_repo_dir
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir)

        if not os.listdir(repo_dir):
            print('cloning repository into directory: {0}'.format(repo_dir))
            Repo.clone_from(self.git_repository, repo_dir)
            print('cloning finished')

        self.repo = Repo(repo_dir)
        assert not self.repo.bare

        self.commits = list(self.repo.iter_commits('master'))
        # self.cc_per_commit = {commit: None for commit in self.commits}
        self.cc_per_commit = {}

        print("Repository setup complete")


    def chunk_form(self,commits):
        length = len(commits)
        step = int(round(length / 2))
        print step
        temp = []
        for i in range(0, length, step):
            temp.append(cc_manager.commits[i:i + step])
        return temp

    def slave_one(self):
        temp = self.chunks.pop(0)
        requests.post(cc_manager.slave_address, data={"data": temp})

    def slave_second(self):
        temp =self.chunks.pop(0)
        requests.post(cc_manager.slave_address_seond, data={"data": self.chunks.pop(0)})

    def queue_formation(self,commits):
        self.chunks = self.chunk_form(commits)
        p1 = Process(target = self.slave_one)
        p1.start()
        p2 = Process(target = self.slave_second)
        p2.start()



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--shost', type=str, default='127.0.0.1', help='host ip of slave.')
    parser.add_argument('--sport', type=int, default=8001, help='port of slave.')
    parser.add_argument('--mport', type=int, default=8003, help='port of slave.')

    FLAGS, unparsed = parser.parse_known_args()

    # global cc_manager

    cc_manager = CodeComplexityMaster(FLAGS.shost,FLAGS.sport,FLAGS.mport)
    cc_manager.setup_gitrepo()
    cc_manager.queue_formation(cc_manager.commits)
    start_time = timeit.default_timer()
    print " START TIME ------------------->", start_time

    app.run(host=FLAGS.shost, port=FLAGS.mport,threaded=True)


