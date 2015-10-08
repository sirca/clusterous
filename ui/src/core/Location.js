

import { canUseDOM } from 'fbjs/lib/ExecutionEnvironment';
import createHistory from 'history/lib/createBrowserHistory';
import useQueries from 'history/lib/useQueries';

const location = canUseDOM ? useQueries(createHistory)() : {};

export default location;
