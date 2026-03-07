// ========================================
// APPLICATION: Main Entry Point
// ========================================

import router from './router.js';
import { HeaderComponent, SidebarComponent, FooterComponent } from './components/index.js';

class App {
  constructor() {
    this.header = new HeaderComponent();
    this.sidebar = new SidebarComponent();
    this.footer = new FooterComponent();
  }

  init() {
    console.log('🚀 Initializing QTDA Application...');

    // Render layout
    const body = document.body;
    const container = document.createElement('div');
    container.className = 'flex flex-col h-screen bg-background-light dark:bg-background-dark';

    // Header
    container.appendChild(this.header.render());

    // Main content area
    const mainContainer = document.createElement('div');
    mainContainer.className = 'flex flex-1 overflow-hidden';
    mainContainer.innerHTML = `
      <div id="app-sidebar"></div>
      <div id="app-content" class="flex-1 overflow-auto"></div>
    `;
    container.appendChild(mainContainer);

    // Sidebar
    const sidebarContainer = document.getElementById('app-sidebar');
    sidebarContainer.appendChild(this.sidebar.render());

    // Footer
    container.appendChild(this.footer.render());

    // Clear body and append
    body.innerHTML = '';
    body.appendChild(container);

    // Initialize router
    router.init();

    console.log('✅ Application ready');
  }
}

// Start app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
