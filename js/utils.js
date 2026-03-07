// Utility Functions
// Các hàm tiện ích chung

/**
 * Hàm lấy dữ liệu từ API
 * @param {string} url - URL của API
 * @returns {Promise}
 */
export async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
}

/**
 * Hàm format ngày
 * @param {Date} date - Đối tượng Date
 * @returns {string}
 */
export function formatDate(date) {
  return new Date(date).toLocaleDateString('vi-VN');
}
