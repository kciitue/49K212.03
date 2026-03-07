// ========================================
// COMPONENT: Header
// ========================================

export class HeaderComponent {
  constructor() {
    this.element = null;
  }

  render() {
    const header = document.createElement('header');
    header.className = 'bg-white dark:bg-[#1a2632] border-b border-gray-200 dark:border-gray-700 px-6 py-4';
    header.innerHTML = `
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-primary">QTDA</h1>
        <nav class="hidden md:flex gap-4">
          <a href="#" class="text-gray-800 dark:text-gray-100 hover:text-primary">Home</a>
          <a href="#" class="text-gray-800 dark:text-gray-100 hover:text-primary">About</a>
          <a href="#" class="text-gray-800 dark:text-gray-100 hover:text-primary">Contact</a>
        </nav>
      </div>
    `;
    return header;
  }
}

// ========================================
// COMPONENT: Sidebar
// ========================================

export class SidebarComponent {
  constructor() {
    this.element = null;
  }

  render() {
    const sidebar = document.createElement('aside');
    sidebar.className = 'w-64 bg-white dark:bg-[#1a2632] border-r border-gray-200 dark:border-gray-700 hidden md:flex flex-col p-6';
    sidebar.innerHTML = `
      <h2 class="text-xl font-bold mb-4">Menu</h2>
      <ul class="space-y-2">
        <li><a href="#" class="block p-2 rounded hover:bg-primary-light dark:hover:bg-gray-700">Dashboard</a></li>
        <li><a href="#" class="block p-2 rounded hover:bg-primary-light dark:hover:bg-gray-700">Settings</a></li>
        <li><a href="#" class="block p-2 rounded hover:bg-primary-light dark:hover:bg-gray-700">Profile</a></li>
      </ul>
    `;
    return sidebar;
  }
}

// ========================================
// COMPONENT: Footer
// ========================================

export class FooterComponent {
  constructor() {
    this.element = null;
  }

  render() {
    const footer = document.createElement('footer');
    footer.className = 'bg-white dark:bg-[#1a2632] border-t border-gray-200 dark:border-gray-700 px-6 py-4 text-center text-gray-600 dark:text-gray-400';
    footer.innerHTML = `
      <p>&copy; 2026 QTDA. All rights reserved.</p>
    `;
    return footer;
  }
}
