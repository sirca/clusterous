

import React, { PropTypes, Component } from 'react';
import classNames from 'classnames';
import styles from './Navigation.css';
import withStyles from '../../decorators/withStyles';
import Link from '../Link';
import Router from 'react-routing/src/Router';

@withStyles(styles)
class Navigation extends Component {

  static propTypes = {
    className: PropTypes.string,
    path: PropTypes.string
  };

  render() {

    console.log('Path From Nav: ' + this.props.path);
    let dashboard = '';
    let create = '';
    let deploy = '';

    if(this.props.path === "/") {
      dashboard = <li className="active"><a href="/" onClick={Link.handleClick}><i className="fa fa-dashboard"></i><span>Dashboard</span></a></li>
    }
    else {
      dashboard = <li><a href="/" onClick={Link.handleClick}><i className="fa fa-dashboard"></i><span>Dashboard</span></a></li>
    }

    if(this.props.path === "/create") {
      create = <li className="active"><a href="/create" onClick={Link.handleClick}><i className="fa fa-edit"></i><span>Create Cluster</span></a></li>
    }
    else {
      create = <li><a href="/create" onClick={Link.handleClick}><i className="fa fa-edit"></i><span>Create Cluster</span></a></li>
    }

    if(this.props.path === "/deploy") {
      deploy = <li className="active"><a href="/deploy" onClick={Link.handleClick}><i className="fa fa-bolt"></i><span>Deploy Environment</span></a></li>
    }
    else {
      deploy = <li><a href="/deploy" onClick={Link.handleClick}><i className="fa fa-bolt"></i><span>Deploy Environment</span></a></li>
    }

    return (
      <div className="main-sidebar">
        <div className="sidebar">
          <div className="user-panel">
            <div className="pull-left image">
              <img src="theme/img/user2-160x160.jpg" className="img-circle" alt="User Image"/>
            </div>
            <div className="pull-left info">
              <p>Tim Berners-Lee</p>

              <a href="#"><i className="fa fa-circle text-success"></i> Online</a>
            </div>
          </div>

          <ul className="sidebar-menu">
            {dashboard}
            {create}
            {deploy}
          </ul>

        </div>
      </div>
    );

  // <div className={classNames(this.props.className, 'Navigation')} role="navigation">
  //       <a className="Navigation-link" href="/about" onClick={Link.handleClick}>About</a>
  //       <a className="Navigation-link" href="/contact" onClick={Link.handleClick}>Contact</a>
  //       <span className="Navigation-spacer"> | </span>
  //       <a className="Navigation-link" href="/login" onClick={Link.handleClick}>Log in</a>
  //       <span className="Navigation-spacer">or</span>
  //       <a className="Navigation-link Navigation-link--highlight" href="/register" onClick={Link.handleClick}>Sign up</a>
  //     </div>
  }

}

export default Navigation;
