

import React, { PropTypes, Component } from 'react';
import styles from './ClusterList.css';
import withStyles from '../../decorators/withStyles';
import Link from '../Link';

@withStyles(styles)
class ClusterList extends Component {

  static propTypes = {
    title: PropTypes.string,
  };

  static contextTypes = {
    onSetTitle: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);

    this.state = {results: [], loading: false};
  }

  componentDidMount() {

    this.setState({loading: true});

    var results = [{
      "clusterName": "mycluster",
      "controllerInstanceType": "t2.medium",
      "sharedVolumeSize": 60,
      "environmentType": "ipython",
      "uptime": 2363463,
      "controllerIP": "123.123.123.123",
      "instanceParameters": {
        "masterInstanceType": "t2.micro",
        "workerInstanceType": "t2.micro",
        "instanceCount": 2
      },
      "runningInstances": {
        "t2.medium": 1,
        "t2.micro": 2
      },
      "status": "running"
    }]

    var promise = new Promise(function(resolve, reject) {
      // do a thing, possibly async, then…

      setTimeout(function() {
        resolve(results);
      }, 2000);

    });

    promise.then(function(result) {
      this.setState({results: result, loading: false});
      console.log('Finished');
    }.bind(this), function(err) {
      console.log(err); // Error: "It broke"
      this.setState({results: [], loading: false});
    }.bind(this));
  }


  render() {
    this.context.onSetTitle(this.props.title);
    let clusterList = this.state.results || [];

    if(this.state.loading) {
      return (
        <div className="box box-warning clusterous-overlay">
          <div className="box-header with-border">
            <h3 className="box-title">Checking Cluster Status...</h3>
          </div>
          <div className="overlay">
            <i className="fa fa-refresh fa-spin"></i>
          </div>
        </div>
      );
    }
    return (
      <div>
        <div className="box box-primary">
          <div className="box-header with-border">
            <h3 className="box-title">Cluster List</h3>
            <div className="box-tools pull-right">
              <button className="btn btn-box-tool" data-widget="collapse"><i className="fa fa-minus"></i></button>
              <button className="btn btn-box-tool" data-widget="remove"><i className="fa fa-times"></i></button>
            </div>
          </div>
          {
            clusterList.map(function(result) {
              let path = '/cluster/' + result.clusterName;

              return (
                <div className="box-body" key={result.clusterName}>
                  <div className="table-responsive">
                    <table className="table no-margin">
                      <thead>
                        <tr>
                          <th>Cluster Name</th>
                          <th>Instances</th>
                          <th>Status</th>
                          <th></th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td><a href={path} onClick={Link.handleClick}>{result.clusterName}</a></td>
                          <td>{result.instanceParameters.instanceCount}</td>
                          <td><span className="label label-success">{result.status}</span></td>
                          <td>
                            <a href={path} onClick={Link.handleClick} className="btn btn-sm btn-default btn-flat pull-left">
                              <span className="fa fa-fw fa-gear" aria-hidden="true"></span> Manage
                            </a>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              );

            })
          }

          <div className="box-footer clearfix">
            <a className="btn btn-sm btn-primary btn-flat pull-right" href="/create" onClick={Link.handleClick}>
              <i className="fa fa-edit clusterous-icon-spacer"></i>
              Create New Cluster
            </a>
          </div>
        </div>
      </div>
    );
  }

}

export default ClusterList;


