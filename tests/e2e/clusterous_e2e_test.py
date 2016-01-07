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

    def test_cluster_create(self):
        # Check cluster status
        cmd = 'status'
        rc, stdout, stderr = self._cli_run(cmd)
        if ('No working cluster has been set' in stderr):
            cmd = 'create data/test-cluster.yml'
            rc, stdout, stderr = self._cli_run(cmd)
            self.assertEqual(rc, 0)
            self.assertRegexpMatches(stderr, 'Cluster "e2etestcluster" created')
 
            # Check if cluster has been created
            cmd = 'status'
            rc, stdout, stderr = self._cli_run(cmd)
            self.assertTrue('e2etestcluster' in stdout and 'running' in stdout)

    def test_cluster_status(self):
        cmd = 'status'
        rc, stdout, stderr = self._cli_run(cmd)
        if ('No working cluster has been set' in stderr):
            self.assertRegexpMatches(stderr, 'No working cluster has been set')
        else:
            self.assertTrue('e2etestcluster' in stdout and 'running' in stdout)

    def test_cluster_run(self):
        cmd = 'status'
        rc, stdout, stderr = self._cli_run(cmd)
        if ('e2etestcluster' in stdout and 'running' in stdout):
            cmd = 'run  data/cluster-envs/basic-python-env.yml'
            rc, stdout, stderr = self._cli_run(cmd)
            self.assertRegexpMatches(stderr, '1 nodes of type "worker" added')

    def test_cluster_add_nodes(self):
        cmd = 'status'
        rc, stdout, stderr = self._cli_run(cmd)
        if ('e2etestcluster' in stdout and 'running' in stdout):
            cmd = 'add-nodes 1'
            rc, stdout, stderr = self._cli_run(cmd)
            self.assertRegexpMatches(stderr, '1 nodes of type "worker" added')
  
    def test_cluster_rm_nodes(self):
        cmd = 'status'
        rc, stdout, stderr = self._cli_run(cmd)
        if ('e2etestcluster' in stdout and 'running' in stdout):
            cmd = 'rm-nodes 1'
            rc, stdout, stderr = self._cli_run(cmd)
            self.assertRegexpMatches(stderr, '1 nodes of type "worker" removed')

    def test_cluster_destroy(self):
        # Check cluster status
        cmd = 'status'
        rc, stdout, stderr = self._cli_run(cmd)
        if (('e2etestcluster' in stdout and 'running' in stdout) or ('destroy' in stderr)):
            # Destroy cluster
            cmd = 'destroy --confirm'
            rc, stdout, stderr = self._cli_run(cmd)
            self.assertEqual(rc, 0)
  
            # Check if cluster has been destroyed
            cmd = 'status'
            rc, stdout, stderr = self._cli_run(cmd)
            self.assertRegexpMatches(stderr, 'No working cluster has been set')

if __name__ == '__main__':
    unittest.main()
