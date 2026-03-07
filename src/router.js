// ========================================
// ROUTER: Simple SPA Router
// ========================================

import { HomePage, DashboardPage } from './pages/index.js';

export class Router {
  constructor() {
    this.routes = {};
    this.currentPage = null;
  }

  register(path, pageClass) {
    this.routes[path] = pageClass;
  }

  async navigate(path) {
    const PageClass = this.routes[path] || this.routes['/'];
    if (!PageClass) {
      console.error(`Route not found: ${path}`);
      return;
    }

    this.currentPage = new PageClass();
    const content = document.getElementById('app-content');
    if (content) {
      content.innerHTML = '';
      content.appendChild(this.currentPage.render());
    }
  }

  init() {
    // Register routes
    this.register('/', HomePage);
    this.register('/dashboard', DashboardPage);

    // Handle navigation
    window.addEventListener('hashchange', () => {
      const path = window.location.hash.slice(1) || '/';
      this.navigate(path);
    });

    // Initial load
    const path = window.location.hash.slice(1) || '/';
    this.navigate(path);
  }
}

export default new Router();
