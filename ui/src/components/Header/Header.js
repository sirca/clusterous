

import React, { PropTypes, Component } from 'react';
import styles from './Header.css';
import withStyles from '../../decorators/withStyles';
import Link from '../Link';
import Navigation from '../Navigation';

@withStyles(styles)
class Header extends Component {

  static propTypes = {
    path: PropTypes.string
  };


  render() {
    return (
      <div>
      <header className="main-header">
      <a href="/" onClick={Link.handleClick} className="logo">
        <span className="logo-lg"><b>Cluster</b>ous</span>
      </a>

      <nav className="navbar navbar-static-top" role="navigation">
        <div className="navbar-custom-menu">
          <ul className="nav navbar-nav">

            <li className="dropdown notifications-menu">
              <a href="#" className="dropdown-toggle" data-toggle="dropdown">
                <i className="fa fa-bell-o"></i>
                <span className="label label-warning">10</span>
              </a>
              <ul className="dropdown-menu">
                <li className="header">You have 10 notifications</li>
                <li>
                  <ul className="menu">
                    <li>
                      <a href="#">
                        <i className="ion ion-ios-people info"></i> Notification title
                      </a>
                    </li>
                  </ul>
                </li>
                <li className="footer"><a href="#">View all</a></li>
              </ul>
            </li>
            <li className="dropdown user user-menu">
              <a href="#" className="dropdown-toggle" data-toggle="dropdown">

                <span className="hidden-xs">Tim Berners-Lee</span>
              </a>
              <ul className="dropdown-menu">
                <li className="user-header">
                  <img src="theme/img/user2-160x160.jpg" className="img-circle" alt="User Image" />
                  <p>
                    Tim Berners-Lee
                    <small>Member since Nov. 2012</small>
                  </p>
                </li>
                <li className="user-body">
                  <div className="col-xs-4 text-center">
                    <a href="#">Notifications</a>
                  </div>
                </li>
                <li className="user-footer">
                  <div className="pull-left">
                    <a href="#" className="btn btn-default btn-flat">Profile</a>
                  </div>
                  <div className="pull-right">
                    <a href="#" className="btn btn-default btn-flat">Sign out</a>
                  </div>
                </li>
              </ul>
            </li>
          </ul>
        </div>
      </nav>
    </header>
    <Navigation path={this.props.path}/>
    </div>
    );
  }

   // <div className="Header">
   //      <div className="Header-container">
   //        <a className="Header-brand" href="/" onClick={Link.handleClick}>
   //          <img className="Header-brandImg" src={require('./logo-small.png')} width="38" height="38" alt="React" />
   //          <span className="Header-brandTxt">Your Company</span>
   //        </a>
   //        <Navigation className="Header-nav" />
   //        <div className="Header-banner">
   //          <h1 className="Header-bannerTitle">React</h1>
   //          <p className="Header-bannerDesc">Complex web apps made easy</p>
   //        </div>
   //      </div>
   //    </div>

}

export default Header;
