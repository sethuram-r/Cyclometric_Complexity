import argparse
import os
from git import Repo
import requests
import numpy as np
import timeit

def get():

    if len(cc_manager.commits) == 0:
        commit_number = 'Done'
    else:
        commit = cc_manager.commits.pop(0)
        commit_number = commit.hexsha
        print("new length of commit_numbers = ", len(cc_manager.commits))
    return commit_number



class CodeComplexityMaster:

    def __init__(self ,slave_ip, slave_port):

        if  slave_ip and  slave_port:
            self.slave_address = "http://{0}:{1}".format(slave_ip, slave_port)
            self.slave_address_seond = "http://{0}:{1}".format(slave_ip, slave_port+1)
            print self.slave_address


        print("Initialising Master...")

        # GIT repository settings
        self.git_repository = "https://github.com/DLTK/DLTK"
        self.root_repo_dir = "./repo"
        self.commits = []
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



    def force_slave(self,length):
        sum = []
        for i in  range(length) :
            print "Master instructs slave..."

            if len(cc_manager.commits) == 0:
                print "Total Cyclometric Complexity is -----------> ", np.sum(sum)
                elapsed = timeit.default_timer() - start_time
                print " ELAPSED TIME ------------------->", elapsed
                break
            response = requests.get(cc_manager.slave_address+"/"+get())
            response_second = requests.get(cc_manager.slave_address_seond + "/" + get())
            if response:
                print "reponse--------->"
                reponse = response.json()
                sum.append(int(reponse['cyclometric_complexity']))
                print 'worker_id', reponse['worker_id']
                print 'commit_number', reponse['commit_number']
                print 'cyclometric complexity', reponse['cyclometric_complexity']
            if response_second:
                print "reponse---second------>"
                response_second = response_second.json()
                sum.append(int(response_second['cyclometric_complexity']))
                print 'worker_id', response_second['worker_id']
                print 'commit_number', response_second['commit_number']
                print 'cyclometric complexity', response_second['cyclometric_complexity']







if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--shost', type=str, default='127.0.0.1', help='host ip of slave.')
    parser.add_argument('--sport', type=int, default=8001, help='port of slave.')

    FLAGS, unparsed = parser.parse_known_args()

    # global cc_manager

    cc_manager = CodeComplexityMaster(FLAGS.shost,FLAGS.sport)
    cc_manager.setup_gitrepo()
    start_time = timeit.default_timer()
    print " START TIME ------------------->", start_time
    cc_manager.force_slave(len(cc_manager.commits))



