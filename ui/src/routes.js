

import React from 'react';
import Router from 'react-routing/src/Router';
import http from './core/HttpClient';
import App from './components/App';
import ContentPage from './components/ContentPage';
import ContactPage from './components/ContactPage';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import NotFoundPage from './components/NotFoundPage';
import ErrorPage from './components/ErrorPage';
import ClusterList from './components/ClusterList';
import CreateCluster from './components/CreateCluster';
import DisplayCluster from './components/DisplayCluster';
import DisplayEnvironment from './components/DisplayEnvironment';

const router = new Router(on => {
  on('*', async (state, next) => {
    const component = await next();
    return component && <App context={state.context} path={state.path}>{component}</App>;
  });

  on('/cluster/:name', async (state) => {
    return <DisplayCluster name={state.params.name} />;
  });

  on('/environment/:name', async (state) => {
    return <DisplayEnvironment name={state.params.name} />;
  });

  on('/', async () => <ClusterList />);

  on('/create', async () => <CreateCluster />);

  on('/contact', async () => <ContactPage />);

  on('/login', async () => <LoginPage />);

  on('/register', async () => <RegisterPage />);

  on('*', async (state) => {
    const content = await http.get(`/api/content?path=${state.path}`);
    return content && <ContentPage {...content} />;
  });

  on('error', (state, error) => state.statusCode === 404 ?
    <App context={state.context} error={error}><NotFoundPage /></App> :
    <App context={state.context} error={error}><ErrorPage /></App>
  );
});

export default router;
