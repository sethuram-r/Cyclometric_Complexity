import numpy as np
import os
from git import Repo
import argparse
from os import walk
import radon
from radon.complexity import cc_rank, cc_visit
from flask import Flask,request,json,jsonify,request
import requests
from threading import Timer
app = Flask(__name__)


class CodeComplexityWorker:

    def __init__(self, worker_id, worker_name, worker_ip, worker_port , master_port):
        # GIT repository settings
        self.worker_id = worker_id
        self.worker_name = worker_name
        self.git_repository = "https://github.com/DLTK/DLTK"
        self.root_repo_dir = "./repo_worker_" + str(worker_id)
        self.master_address = "http://{0}:{1}".format(worker_ip, master_port)

        self.repo = None
        self.files = []
        self.cc_files = {}
        self.setup_gitrepo()

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

        # setup list of all .py files from most recent commit
        self.update_files()

    def set_commit_state(self, commit_number):
        """ sets repository state to the provided commit"""

        print("setting repository state to: {0}".format(commit_number))

        # use checkout from git
        git = self.repo.git
        git.checkout(commit_number)

        # refresh list of all .py files
        self.update_files()

    def update_files(self):
        """ get all files from current commit"""

        self.files = []
        for (dirpath, dirnames, filenames) in walk(self.root_repo_dir):
            for filename in filenames:
                if '.py' in filename:
                    dirpath = dirpath.replace("\\", "/")
                    self.files.append(dirpath + '/' + filename)

        # reset code complexity results for each file
        self.cc_files = {file: None for file in self.files}

    def calculate_cyclomatic_complexity(self, commit_number):
        """ calculate cc for all files in current commit """

        for file in self.files:
            with open(file) as f:
                data = f.read()
                try:
                    cc = radon.complexity.cc_visit(data)
                    cc_tot = 0
                    for cc_item in cc:
                        cc_tot += cc_item.complexity
                        # print("complexity = ", cc_item.complexity)
                except Exception as err:
                    print("ERROR: could not calculate cc for file {0} in commit {1}".format(file, commit_number))
                    print(err)
                    cc_tot = 0

                self.cc_files[file] = cc_tot

        # return total complexity of all files
        return sum(self.cc_files.values())


    def respond_to_request(self,key):

        print "request came"
        # checkout to commit number:
        self.set_commit_state(key)

        # calculate cyclomatic complexity
        print('worker {0} - calculating commit {1}'.format(self.worker_name, key))

        return self.calculate_cyclomatic_complexity(key)


def call_back():
    requests.post(worker.master_address,json=worker.msg)




@app.route('/', methods=['GET', 'POST'])
def get():
    sum = []
    for i in request.form.getlist('data'):
        sum.append(worker.respond_to_request(i))
    total_cyclometric_complexity_this_chunk = np.sum(sum)

    print "total_cyclometric_complexity_this_chunk------------->",total_cyclometric_complexity_this_chunk
    post_msg = {'worker_id': worker.worker_id,'total_cyclometric_complexity': str(total_cyclometric_complexity_this_chunk)}
    worker.msg = post_msg
    t = Timer(5.0, call_back)
    t.start()

    return "success"




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--workerID',type=int,default=2,help='ID to identify worker')
    parser.add_argument('--shost', type=str, default='127.0.0.1', help='host ip of slave.')
    parser.add_argument('--sport', type=int, default=8002, help='port of slave.')
    parser.add_argument('--mport', type=int, default=8003, help='port of master.')

    FLAGS, unparsed = parser.parse_known_args()

    worker_name = 'worker_{0}'.format(FLAGS.workerID)
    worker = CodeComplexityWorker(FLAGS.workerID, worker_name, FLAGS.shost, FLAGS.sport,FLAGS.mport)

       # run application with set parameters
    app.run(host=FLAGS.shost, port=FLAGS.sport,threaded=True)

