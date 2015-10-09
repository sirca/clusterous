

import React, { PropTypes, Component } from 'react';
import styles from './CreateCluster.css';
import withStyles from '../../decorators/withStyles';
import Link from '../Link';

@withStyles(styles)
class CreateCluster extends Component {

  static propTypes = {
    title: PropTypes.string,
  };

  static contextTypes = {
    onSetTitle: PropTypes.func.isRequired,
  };

  constructor() {
    super();

    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleCreate = this.handleCreate.bind(this);

    this.state = {
      typeOfSubmit: '',
      created: false,
      error: false
    };
  }

  handleSubmit(e) {
    e.preventDefault();

    if (this.state.typeOfSubmit === 'create') {

      var clusterName = ReactDOM.findDOMNode(this.refs.clusterName).value.trim();
      var instanceCount = ReactDOM.findDOMNode(this.refs.instanceCount).value.trim();
      var controllerInstanceType = ReactDOM.findDOMNode(this.refs.controllerInstanceType).value.trim();
      var masterInstanceType = ReactDOM.findDOMNode(this.refs.masterInstanceType).value.trim();
      var workerInstanceType = ReactDOM.findDOMNode(this.refs.workerInstanceType).value.trim();
      var environmentType = ReactDOM.findDOMNode(this.refs.environmentType).value.trim();
      var sharedVolumeSize = ReactDOM.findDOMNode(this.refs.sharedVolumeSize).value.trim();

      var data = {
        "clusterName": clusterName,
        "controllerInstanceType": controllerInstanceType,
        "sharedVolumeSize": sharedVolumeSize,
        "environmentType": environmentType,
        "instanceParameters": {
          "masterInstanceType": masterInstanceType,
          "workerInstanceType": workerInstanceType,
          "instanceCount": instanceCount
          }
      };

      $.ajax({
        url: this.props.source,
        dataType: 'json',
        crossDomain: true,
        type: 'POST',
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
          console.log('Success: ', data);
          this.setState({created: true})
        }.bind(this),
        error: function(xhr, status, err) {
          console.log('Failed: ', status);
        }.bind(this)
      });

      ReactDOM.findDOMNode(this.refs.clusterName).value = '';
      ReactDOM.findDOMNode(this.refs.instanceCount).value = '';
      ReactDOM.findDOMNode(this.refs.controllerInstanceType).value = '';
      ReactDOM.findDOMNode(this.refs.masterInstanceType).value = '';
      ReactDOM.findDOMNode(this.refs.workerInstanceType).value = '';
      ReactDOM.findDOMNode(this.refs.environmentType).value = '';
      ReactDOM.findDOMNode(this.refs.sharedVolumeSize).value = '';

      console.log('Created...');
    }
    else {
      console.log('Different Submit');
    }

    return;
  }

  handleCreate() {
    this.setState({typeOfSubmit: 'create'}, this.refs.form.submit);
  }

  render() {

    this.context.onSetTitle(this.props.title);

    if(this.state.created) {
      return(
        <div className="alert alert-success alert-dismissible">
          <button type="button" className="close" data-dismiss="alert" aria-hidden="true">×</button>
          <h4>  <i className="icon fa fa-check"></i> Congratulations!</h4>
          Your cluster is being created
        </div>
      )
    }
    else {
      return (

        <div className="box box-primary">
          <div className="box-header with-border">
            <h3 className="box-title">Create Cluster</h3>
          </div>
          <form className="form-horizontal" onSubmit={this.handleSubmit} ref="form">
            <div className="box-body">
              <div className="form-group">
                <label htmlFor="clusterName" className="col-sm-3 control-label">Cluster Name</label>
                <div className="col-sm-3">
                  <input type="text" className="form-control" id="clusterName" placeholder="eg. My Spark Cluster" ref="clusterName" />
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="instanceCount" className="col-sm-3 control-label">Instance Count</label>
                <div className="col-sm-3">
                  <input type="text" className="form-control" id="instanceCount" placeholder="eg. 8" ref="instanceCount" />
                </div>

                <label htmlFor="controllerInstanceType" className="col-sm-3 control-label">Controller Instance Type</label>
                <div className="col-sm-3">
                  <select className="form-control" ref="controllerInstanceType">
                    <option>t2.micro</option>
                    <option>t2.small</option>
                    <option>t2.medium</option>
                    <option>t2.large</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="masterInstanceType" className="col-sm-3 control-label">Master Instance Type</label>
                <div className="col-sm-3">
                  <select className="form-control" ref="masterInstanceType">
                    <option>t2.micro</option>
                    <option>t2.small</option>
                    <option>t2.medium</option>
                    <option>t2.large</option>
                  </select>
                </div>
                <label htmlFor="workerInstanceType" className="col-sm-3 control-label">Worker Instance Type</label>
                <div className="col-sm-3">
                  <select className="form-control" ref="workerInstanceType">
                    <option>t2.micro</option>
                    <option>t2.small</option>
                    <option>t2.medium</option>
                    <option>t2.large</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="environmentType" className="col-sm-3 control-label">Environment Type</label>
                <div className="col-sm-3">
                  <select className="form-control" ref="environmentType">
                    <option>iPython</option>
                    <option>Spark</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="sharedVolumeSize" className="col-sm-3 control-label">Shared Volume Size (GB)</label>
                <div className="col-sm-3">
                  <input type="text" className="form-control" id="sharedVolumeSize" placeholder="eg. 8"  ref="sharedVolumeSize"/>
                </div>
              </div>
            </div>
            <div className="box-footer">
              <a href="/" onClick={Link.handleClick} className="btn btn-default btn-flat">
                Cancel
              </a>
              <button className="btn btn-primary pull-right btn-flat" onClick={this.handleCreate}>
                <i className="fa fa-edit clusterous-icon-spacer"></i>
                Create
              </button>
            </div>
          </form>
        </div>


      );
    }
  }

}

export default CreateCluster;


