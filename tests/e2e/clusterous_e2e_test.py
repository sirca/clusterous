import sys
import boto
from StringIO import StringIO

from mock import MagicMock
import unittest

from clusterous.cli import main

class ClusterE2ETest(unittest.TestCase):
    def _cli_run(self, cmd):
        stdout, stderr = StringIO(), StringIO()
        sys.stdout, sys.stderr = stdout, stderr
        rc = main(cmd.split())
        return rc, stdout.getvalue(), stderr.getvalue()

    def _cluster_destroy(self):
        rc, stdout, stderr = self._cli_run('destroy --confirm')
        return rc == 0 and self._no_cluster_running()

    def _no_cluster_running(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and 'No working cluster has been set' in stderr

    def _cluster_running(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and 'e2etestcluster' in stdout and 'running' in stdout

    def _cluster_wrong_state(self):
        rc, stdout, stderr = self._cli_run('status')
        return rc == 0 and 'destroy' in stderr

    def test_cluster_create(self):
        # Destroy if cluster present
        if self._cluster_running() or self._cluster_wrong_state():
            self._cluster_destroy()

        # Create cluster
        rc, stdout, stderr = self._cli_run('create data/test-cluster.yml')
        self.assertEqual(rc, 0)
        self.assertRegexpMatches(stderr, 'Cluster "e2etestcluster" created')
        self.assertTrue(self._cluster_running())
 
    def test_cluster_status(self):
        if self._cluster_running():
            rc, stdout, stderr = self._cli_run('status')
            self.assertTrue('e2etestcluster' in stdout and 'running' in stdout)

#     def test_cluster_run(self):
#         if self._cluster_running():
#             rc, stdout, stderr = self._cli_run('run  data/cluster-envs/basic-python-env.yml')
#             self.assertRegexpMatches(stderr, '1 nodes of type "worker" added')

    def test_cluster_add_nodes(self):
        if self._cluster_running():
            rc, stdout, stderr = self._cli_run('add-nodes 1')
            self.assertRegexpMatches(stderr, '1 nodes of type "worker" added')
  
    def test_cluster_rm_nodes(self):
        if self._cluster_running():
            rc, stdout, stderr = self._cli_run('rm-nodes 1')
            self.assertRegexpMatches(stderr, '1 nodes of type "worker" removed')

    def test_cluster_destroy(self):
        if self._cluster_running() or self._cluster_wrong_state():
            rc, stdout, stderr = self._cli_run('destroy --confirm')
            self.assertEqual(rc, 0)
            self.assertTrue(self._no_cluster_running())

if __name__ == '__main__':
    unittest.main()
