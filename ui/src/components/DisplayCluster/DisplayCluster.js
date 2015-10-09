import React, { PropTypes, Component } from 'react';
import styles from './DisplayCluster.css';
import withStyles from '../../decorators/withStyles';
import Link from '../Link';
import { Panel, ListGroup, ListGroupItem, Table, ButtonToolbar,
  Button, Input, DropdownButton, MenuItem } from 'react-bootstrap';

@withStyles(styles)
class DisplayCluster extends Component {

  static propTypes = {
    name: PropTypes.string.isRequired,
    title: PropTypes.string,
    pollInterval: PropTypes.number
  };

  static defaultProps = {
    pollInterval: 2000,
  };

  static contextTypes = {
    onSetTitle: PropTypes.func.isRequired,
  };

  constructor(props) {
    super(props);

    this.handleUpdate = this.handleUpdate.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleOnChange = this.handleOnChange.bind(this);
    this.loadCluster = this.loadCluster.bind(this);

    this.state = {
      instanceCount: 0,
      check: false,
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

  loadCluster() {
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
    var check = this.state.check;

    var promise = new Promise(function(resolve, reject) {

      setTimeout(function() {
        if(check) {
          resolve(clusterResult);
        }
        else {
          reject(clusterResult);
        }
      }, 2000);

    });

    promise.then(function(res) {
      this.setState({result: res, loading: false, instanceCount: res.instanceParameters.instanceCount, check:true});

      clearInterval(this.interval);

    }.bind(this), function(err) {
      console.log('Finished Broke');
      console.log(err); // Error: "It broke"
      this.setState({result: {}, loading: false, instanceCount: 0, check:true});
    }.bind(this));
  }

  componentDidMount() {

    this.loadCluster();

    if(!this.state.check) {
      this.interval = setInterval(this.loadCluster, this.props.pollInterval);
    }
    else {
      clearInterval(this.interval);
    }
  }

  componentWillUnmount() {
    clearInterval(this.interval);
    this.loadInterval && clearInterval(this.loadInterval);
    this.loadInterval = false;
  }

  handleSubmit(e) {
    e.preventDefault();

    if (this.state.typeOfSubmit === 'update') {
      console.log('Updating ...');
      this.setState({updated: true})
    }
    else if (this.state.typeOfSubmit === 'delete') {
      console.log('Deleting..');
    }
    else {
      console.log('OTHER..');
    }

    return;
  }

  handleOnChange(event) {
    this.setState({instanceCount: event.target.value})
  }

  handleUpdate() {
    this.setState({typeOfSubmit: 'update'}, this.refs.form.submit);
  }

  handleDelete() {
    this.setState({typeOfSubmit: 'delete'}, this.refs.form.submit);
  }

  render() {

    this.context.onSetTitle(this.props.title);
    let clusterInfo = this.state.result;
    var count = this.state.instanceCount;
    let checked = this.state.check;
    let displayEnvironmentPath = '/environment/' + clusterInfo.clusterName;

    if(this.state.loading && !checked) {
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
    else if(!Object.keys(clusterInfo).length && checked) {
      return (
        <div className="box box-warning clusterous-overlay">
          <div className="box-header with-border">
            <h3 className="box-title">Cluster not up yet... ill keep checking mate - I GOT THIS!</h3>
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
          <form onSubmit={this.handleSubmit} ref="form">
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
                </tbody>
              </table>
            </div>
            <div className="box-footer clearfix">
              <div className="pull-left">
                <button className="btn btn-sm btn-primary btn-flat pull-left" onClick={this.handleUpdate}>
                  <i className="fa fa-save clusterous-icon-spacer"></i>Update Cluster
                </button>&nbsp;&nbsp;
                <a className="btn btn-sm btn-default btn-flat" href={displayEnvironmentPath} onClick={Link.handleClick}>
                  <i className="fa fa-globe clusterous-icon-spacer"></i>Display Environment Details
                </a>
              </div>

              <button className="btn btn-sm btn-danger btn-flat pull-right" onClick={this.handleDelete}>
                <i className="fa fa-remove clusterous-icon-spacer"></i>
                Delete Cluster
              </button>
            </div>
          </form>
        </div>
      );
    }
  }

}

export default DisplayCluster;


