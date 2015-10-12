import React, { PropTypes, Component } from 'react';
import styles from './DisplayCluster.css';
import withStyles from '../../decorators/withStyles';
import ReactDOM from 'react-dom';
import Link from '../Link';
import { Panel, ListGroup, ListGroupItem, Table, ButtonToolbar,
  Button, Input, DropdownButton, MenuItem } from 'react-bootstrap';

@withStyles(styles)
class DisplayCluster extends Component {

  static propTypes = {
    name: PropTypes.string.isRequired,
    title: PropTypes.string,
    pollInterval: PropTypes.number,
    source: PropTypes.string
  };

  static defaultProps = {
    pollInterval: 2000,
    source: 'http://localhost:5005/cluster'
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
      loading: false,
      deleted: false,
      updated: false
    }

  }

  loadCluster() {
    this.setState({loading: true});


    $.ajax({
      url: this.props.source + '/' + this.props.name,
      dataType: 'json',
      crossDomain: true,
      type: 'GET',
      contentType: "application/json; charset=utf-8",
      success: function(data) {
        console.log('Success: ', data);

        if(data && data.status === 'starting') {
          this.setState({result: {}, loading: false, instanceCount: 0, check:true});
        }
        else {
          this.setState({result: data, loading: false, instanceCount: data.instanceParameters.instanceCount, check:true});
          clearInterval(this.interval);
        }
      }.bind(this),
      error: function(xhr, status, err) {
        console.log('Failed: ', status);
        this.setState({result: {}, loading: false, instanceCount: 0, check:true});
      }.bind(this)
    });

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

      var instanceCount = ReactDOM.findDOMNode(this.refs.instanceCount).value.trim();

      var data = {
        instanceCount: instanceCount,
      }

      if (!instanceCount) {
        return;
      }

      $.ajax({
        url: this.props.source,
        dataType: 'json',
        crossDomain: true,
        type: 'PUT',
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
          console.log('Success: ', data);
          this.setState({updated: true, loading: false})
        }.bind(this),
        error: function(xhr, status, err) {
          console.log('Failed: ', status);
          this.setState({loading: false})
        }.bind(this)
      });

      ReactDOM.findDOMNode(this.refs.instanceCount).value = '';

    }
    else if (this.state.typeOfSubmit === 'delete') {
      console.log('Deleting..');

      this.setState({loading: true});

      $.ajax({
        url: this.props.source + '/' + this.props.name,
        dataType: 'json',
        crossDomain: true,
        type: 'DELETE',
        contentType: "application/json; charset=utf-8",
        success: function(data) {
          console.log('Success: ', data);
          this.setState({deleted: true, loading: false})
        }.bind(this),
        error: function(xhr, status, err) {
          console.log('Failed: ', status);
          this.setState({loading: false})
        }.bind(this)
      });
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

    if(this.state.deleted) {
      return (
        <div className="alert alert-success alert-dismissible">
          <button type="button" className="close" data-dismiss="alert" aria-hidden="true">×</button>
          <h4>  <i className="icon fa fa-check"></i> Cluster Deleted.</h4>
          <a className="btn btn-sm btn-default btn-flat" href='/' onClick={Link.handleClick}>
            OK
          </a>
        </div>
      );
    }
    else if(this.state.loading && !checked) {
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
            <h3 className="box-title">Cluster not up yet... please make a coffee and come back soon</h3>
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
                  <th>Environment URL</th>
                  <td><a href={clusterInfo.environmentUrl} target="_blank">{clusterInfo.environmentUrl}</a></td>
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


