

import React, { Component, PropTypes } from 'react';
import { googleAnalyticsId } from '../../config';

class Html extends Component {

  // static propTypes = {
  //   title: PropTypes.string,
  //   description: PropTypes.string,
  //   css: PropTypes.string,
  //   body: PropTypes.string.isRequired,
  // };

  // static defaultProps = {
  //   title: '',
  //   description: '',
  // };

  trackingCode() {
    return ({__html:
      `(function(b,o,i,l,e,r){b.GoogleAnalyticsObject=l;b[l]||(b[l]=` +
      `function(){(b[l].q=b[l].q||[]).push(arguments)});b[l].l=+new Date;` +
      `e=o.createElement(i);r=o.getElementsByTagName(i)[0];` +
      `e.src='https://www.google-analytics.com/analytics.js';` +
      `r.parentNode.insertBefore(e,r)}(window,document,'script','ga'));` +
      `ga('create','${googleAnalyticsId}','auto');ga('send','pageview');`,
    });
  }

  render() {
    return (
      <html className="no-js" lang="">
      <head>
        <meta charSet="utf-8" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
        <title>{this.props.title}</title>
        <meta name="description" content={this.props.description} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="apple-touch-icon" href="apple-touch-icon.png" />
        <style id="css" dangerouslySetInnerHTML={{__html: this.props.css}} />

        <link href="theme/css/bootstrap.min.css" rel="stylesheet" type="text/css" />
        <link href="https://maxcdn.bootstrapcdn.com/font-awesome/4.3.0/css/font-awesome.min.css" rel="stylesheet" type="text/css" />
        <link href="http://code.ionicframework.com/ionicons/2.0.0/css/ionicons.min.css" rel="stylesheet" type="text/css" />
        <link href="theme/css/AdminLTE.css" rel="stylesheet" type="text/css" />
        <link href="theme/css/skins/skin-blue.min.css" rel="stylesheet" type="text/css" />
      </head>
      <body className="skin-blue layout-boxed">
        <div id="app" dangerouslySetInnerHTML={{__html: this.props.body}} className="wrapper" />
        <script src="/app.js"></script>
        <script dangerouslySetInnerHTML={this.trackingCode()} />

        <script src="jQuery-2.1.4.min.js"></script>
        <script src="bootstrap.min.js"></script>
        <script src="fastclick.min.js"></script>
        <script src="app.min.js"></script>

      </body>
      </html>
    );
  }

}

Html.propTypes = {
  title: PropTypes.string,
  description: PropTypes.string,
  css: PropTypes.string,
  body: PropTypes.string.isRequired,
};

Html.defaultProps = {
  title: '',
  description: '',
};

export default Html;
