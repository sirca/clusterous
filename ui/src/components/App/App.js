import React, { PropTypes, Component } from 'react';
import styles from './App.css';
import withContext from '../../decorators/withContext';
import withStyles from '../../decorators/withStyles';
import Header from '../Header';
import Feedback from '../Feedback';
import Footer from '../Footer';

@withContext
@withStyles(styles)
class App extends Component {

  static propTypes = {
    children: PropTypes.element.isRequired,
    error: PropTypes.object,
    path: PropTypes.string
  };

  constructor(props) {
    super(props);
  }

  render() {

    return !this.props.error ? (
      <div>
        <Header path={this.props.path}/>
        <div className="content-wrapper">
            <section className="content">
              {this.props.children}
            </section>
        </div>
        <Footer />
      </div>
    ) : this.props.children;
  }

}

export default App;
