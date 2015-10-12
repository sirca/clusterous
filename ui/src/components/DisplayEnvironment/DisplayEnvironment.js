

import React, { PropTypes, Component } from 'react';
import styles from './DisplayEnvironment.css';
import withStyles from '../../decorators/withStyles';
import Link from '../Link';

@withStyles(styles)
class DisplayEnvironment extends Component {


  static propTypes = {
    name: PropTypes.string.isRequired,
    title: PropTypes.string,
    source: PropTypes.string
  };

  static contextTypes = {
    onSetTitle: PropTypes.func.isRequired,
  };

  static defaultProps = {
    source: 'http://localhost:5000/environment'
  };

  constructor(props) {
    super(props);

    this.handleDelete = this.handleDelete.bind(this);
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


  handleOnChange(event) {
    this.setState({instanceCount: event.target.value})
  }

  handleSubmit(e) {
    e.preventDefault();

    if (this.state.typeOfSubmit === 'delete') {
      console.log('Deleting..');

      $.ajax({
        url: this.props.source,
        dataType: 'json',
        crossDomain: true,
        type: 'DELETE',
        contentType: "application/json; charset=utf-8",
        success: function(data) {
          console.log('Success: ', data);

           this.setState({deleted: true});
        }.bind(this),
        error: function(xhr, status, err) {
          console.log('Failed: ', status);
        }.bind(this)
      });

    }
    else {
      console.log('OTHER..');
    }

    return;
  }

  handleDelete() {
    this.setState({typeOfSubmit: 'delete'}, this.refs.form.submit);
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

    if(this.state.deleted) {
      return (
        <div className="alert alert-success alert-dismissible">
          <button type="button" className="close" data-dismiss="alert" aria-hidden="true">×</button>
          <h4>  <i className="icon fa fa-check"></i> Removed!</h4>
          Your environment has been removed
        </div>
      )
    }
    if(this.state.loading) {
      return (
        <div className="box box-warning clusterous-overlay">
          <div className="box-header with-border">
            <h3 className="box-title">Checking Environment...</h3>
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
              <h3 className="box-title">{clusterInfo.clusterName} Environment</h3>
              <span className="label label-success pull-right">{clusterInfo.status}</span>
            </div>
            <div className="box-body">

              <table className="table">
                <tbody>
                <tr>
                  <th>Environment Type</th>
                  <td>{clusterInfo.environmentType}</td>
                </tr>
                <tr>
                  <th>Environment URL</th>
                  <td><a href={clusterInfo.environmentUrl} target="_blank">{clusterInfo.environmentUrl}</a></td>
                </tr>
                </tbody>
              </table>
            </div>
            <div className="box-footer clearfix">
              <button type="submit" className="btn btn-sm btn-danger btn-flat pull-right" onClick={this.handleDelete}>
                <i className="fa fa-remove clusterous-icon-spacer"></i>
                Remove Environment
              </button>
            </div>
          </form>
        </div>
      );
    }
  }

}

export default DisplayEnvironment;


