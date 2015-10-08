

import React, { PropTypes, Component } from 'react';
import styles from './DisplayEnvironment.css';
import withStyles from '../../decorators/withStyles';
import Link from '../Link';

@withStyles(styles)
class DisplayEnvironment extends Component {


  static propTypes = {
    name: PropTypes.string.isRequired,
    title: PropTypes.string,
  };

  static contextTypes = {
    onSetTitle: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);

    this.updateCluster = this.updateCluster.bind(this);
    this.deleteCluster = this.deleteCluster.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleOnChange = this.handleOnChange.bind(this);

    this.state = {
      instanceCount: 0,
      result: {
        "clusterName": "",
        "controllerInstanceType": "",
        "sharedVolumeSize": 0,
        "environmentType": "",
        "uptime": 0,
        "controllerIP": "",
        "instanceParameters": {
          "masterInstanceType": "",
          "workerInstanceType": "",
          "instanceCount": 0
        },
        "runningInstances": {
          "t2.medium": 0,
          "t2.micro": 0
        },
        "status": ""
      },
      loading: false
    }

  }

  componentDidMount() {

    this.setState({loading: true});

    var clusterResult = {
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
    }

    var promise = new Promise(function(resolve, reject) {
      // do a thing, possibly async, then…

      setTimeout(function() {
        resolve(clusterResult);
      }, 2000);

    });

    promise.then(function(res) {
      this.setState({result: res, loading: false, instanceCount: res.instanceParameters.instanceCount});
      console.log('Finished');

    }.bind(this), function(err) {
      console.log(err); // Error: "It broke"
      this.setState({result: {}, loading: false, instanceCount: 0});
    }.bind(this));
  }

  updateCluster() {

  }

  deleteCluster() {

  }

  handleSubmit() {

  }

  handleOnChange(event) {
    this.setState({instanceCount: event.target.value})
  }

  render() {

    console.log('Name: ' + this.props.name);
    this.context.onSetTitle(this.props.title);
    let clusterInfo = this.state.result;
    var count = this.state.instanceCount;

    console.log('Cluster Info: ' + JSON.stringify(clusterInfo));

    // <div className="box box-warning">
    //     <div className="box-header with-border">
    //       <h3 className="box-title">Checking Cluster Status...</h3>
    //     </div>
    //     <div className="overlay">
    //       <i className="fa fa-refresh fa-spin"></i>
    //     </div>
    //   </div>

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
    else {

      return (

        <div className="box box-success">
          <form onSubmit={this.handleSubmit}>
            <div className="box-header with-border">
              <h3 className="box-title">{clusterInfo.clusterName}</h3>
              <span className="label label-success pull-right">{clusterInfo.status}</span>
            </div>
            <div className="box-body">

              <table className="table">
                <tbody>
                <tr>
                  <th>Name</th>
                  <td>{clusterInfo.clusterName}</td>
                </tr>
                <tr>
                  <th>Instance Count</th>
                  <td>
                    <input ref="instanceCount" type="text" className="form-control" id="instanceCount" placeholder="eg. 8" onChange={this.handleOnChange} value={count} />
                  </td>
                </tr>
                <tr>
                  <th>Controller Instance Type</th>
                  <td>{clusterInfo.controllerInstanceType}</td>
                </tr>
                <tr>
                  <th>Master Instance Type</th>
                  <td>{clusterInfo.instanceParameters.masterInstanceType}</td>
                </tr>
                <tr>
                  <th>Worker Instance Type</th>
                  <td>{clusterInfo.instanceParameters.workerInstanceType}</td>
                </tr>
                <tr>
                  <th>Environment Type</th>
                  <td>{clusterInfo.environmentType}</td>
                </tr>
                <tr>
                  <th>Shared Volume Size (GB)</th>
                  <td>{clusterInfo.sharedVolumeSize}</td>
                </tr>
                <tr>
                  <th>Up time</th>
                  <td>{clusterInfo.uptime}</td>
                </tr>
                <tr>
                  <th>Controller IP</th>
                  <td>{clusterInfo.controllerIP}</td>
                </tr>
                <tr>
                  <th>Up time</th>
                  <td>{clusterInfo.uptime}</td>
                </tr>
                </tbody>
              </table>
            </div>
            <div className="box-footer clearfix">
              <div className="pull-left">
                <a className="btn btn-sm btn-primary btn-flat pull-left" href="/create" onClick={Link.handleClick}>
                  <i className="fa fa-save clusterous-icon-spacer"></i>Update Cluster
                </a>&nbsp;&nbsp;
                <a className="btn btn-sm btn-default btn-flat" href="/create" onClick={Link.handleClick}>
                  <i className="fa fa-globe clusterous-icon-spacer"></i>Display Environment Details
                </a>
              </div>

              <a className="btn btn-sm btn-warning btn-flat pull-right" href="/create" onClick={Link.handleClick}>
                <i className="fa fa-remove clusterous-icon-spacer"></i>
                Delete Cluster
              </a>
            </div>
          </form>
        </div>
      );
    }
  }

}

export default DisplayEnvironment;


