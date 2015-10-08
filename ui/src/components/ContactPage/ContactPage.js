

import React, { PropTypes, Component } from 'react';
import styles from './ContactPage.css';
import withStyles from '../../decorators/withStyles';

@withStyles(styles)
class ContactPage extends Component {

  static contextTypes = {
    onSetTitle: PropTypes.func.isRequired,
  };

  render() {
    const title = 'Contact Us';
    this.context.onSetTitle(title);
    return (
      <div className="row">
        <div className="col-md-12">

          <div className="box box-default">
            <div className="box-header with-border">
              <h3 className="box-title">Collapsable</h3>
              <div className="box-tools pull-right">
                <button className="btn btn-box-tool" data-widget="collapse"><i className="fa fa-minus"></i></button>
              </div>
            </div>
            <div className="box-body">
              The body of the box
            </div>
          </div>


        </div>

      </div>


    );
  }


  // <div className="ContactPage">
  //       <div className="ContactPage-container">
  //         <h1>{title}</h1>
  //         <p>...</p>
  //       </div>
  //     </div>

}

export default ContactPage;
