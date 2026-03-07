// ========================================
// PAGE: Home
// ========================================

export class HomePage {
  constructor() {
    this.title = 'Home';
  }

  render() {
    const container = document.createElement('main');
    container.className = 'flex-1 overflow-auto';
    container.innerHTML = `
      <div class="p-8">
        <h2 class="text-3xl font-bold mb-4">Welcome to QTDA</h2>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          Đây là một ứng dụng frontend chuẩn được xây dựng với Tailwind CSS và Vanilla JavaScript
        </p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 bg-white dark:bg-[#1a2632] rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 class="font-bold mb-2">Feature 1</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">Mô tả tính năng 1</p>
          </div>
          <div class="p-4 bg-white dark:bg-[#1a2632] rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 class="font-bold mb-2">Feature 2</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">Mô tả tính năng 2</p>
          </div>
          <div class="p-4 bg-white dark:bg-[#1a2632] rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 class="font-bold mb-2">Feature 3</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">Mô tả tính năng 3</p>
          </div>
        </div>
      </div>
    `;
    return container;
  }
}

// ========================================
// PAGE: Dashboard
// ========================================

export class DashboardPage {
  constructor() {
    this.title = 'Dashboard';
  }

  render() {
    const container = document.createElement('main');
    container.className = 'flex-1 overflow-auto';
    container.innerHTML = `
      <div class="p-8">
        <h2 class="text-3xl font-bold mb-4">Dashboard</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-6 bg-white dark:bg-[#1a2632] rounded-lg border border-gray-200 dark:border-gray-700">
            <h4 class="font-bold mb-2">Statistics</h4>
            <p class="text-2xl font-bold text-primary">1,234</p>
          </div>
          <div class="p-6 bg-white dark:bg-[#1a2632] rounded-lg border border-gray-200 dark:border-gray-700">
            <h4 class="font-bold mb-2">Active Users</h4>
            <p class="text-2xl font-bold text-primary">567</p>
          </div>
        </div>
      </div>
    `;
    return container;
  }
}
