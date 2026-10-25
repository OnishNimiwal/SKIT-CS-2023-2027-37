import { useEffect, useState } from 'react';

// Tiny hash router (#/uploads) so the dashboard needs no extra dependency.
export default function useHashRoute(defaultRoute = 'overview') {
  const read = () => window.location.hash.replace(/^#\/?/, '') || defaultRoute;
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const onChange = () => setRoute(read());
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return route;
}
