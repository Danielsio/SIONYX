import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { exportToCSV, exportToExcel, exportToPDF } from './csvExport';

describe('csvExport', () => {
  let clickedLink;
  let createdUrl;
  let revokedUrl;

  beforeEach(() => {
    clickedLink = null;
    createdUrl = null;
    revokedUrl = null;

    vi.stubGlobal('URL', {
      createObjectURL: (blob) => {
        createdUrl = blob;
        return 'blob:mock-url';
      },
      revokeObjectURL: (url) => {
        revokedUrl = url;
      },
    });

    vi.stubGlobal('document', {
      createElement: (_tag) => {
        const el = { href: '', download: '', click: () => { clickedLink = el; } };
        return el;
      },
    });

    vi.stubGlobal('Blob', class MockBlob {
      constructor(parts, options) {
        this.parts = parts;
        this.options = options;
        this.content = parts.join('');
      }
    });
  });

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
    { title: 'City', dataIndex: 'city' },
  ];

  it('should not export when data is null', () => {
    exportToCSV(null, columns, 'test');
    expect(clickedLink).toBeNull();
  });

  it('should not export when data is empty array', () => {
    exportToCSV([], columns, 'test');
    expect(clickedLink).toBeNull();
  });

  it('should export basic data correctly', () => {
    const data = [
      { name: 'Alice', age: 30, city: 'NYC' },
      { name: 'Bob', age: 25, city: 'LA' },
    ];

    exportToCSV(data, columns, 'users');

    expect(clickedLink).not.toBeNull();
    expect(clickedLink.download).toBe('users.csv');
    expect(clickedLink.href).toBe('blob:mock-url');
    expect(revokedUrl).toBe('blob:mock-url');

    const csvContent = createdUrl.content;
    expect(csvContent).toContain('\uFEFF'); // BOM
    expect(csvContent).toContain('Name,Age,City');
    expect(csvContent).toContain('Alice,30,NYC');
    expect(csvContent).toContain('Bob,25,LA');
  });

  it('should handle missing fields as empty strings', () => {
    const data = [{ name: 'Alice' }];
    exportToCSV(data, columns, 'test');

    const csvContent = createdUrl.content;
    expect(csvContent).toContain('Alice,,');
  });

  it('should escape commas in values', () => {
    const data = [{ name: 'Doe, John', age: 30, city: 'NYC' }];
    exportToCSV(data, columns, 'test');

    const csvContent = createdUrl.content;
    expect(csvContent).toContain('"Doe, John"');
  });

  it('should escape double quotes in values', () => {
    const data = [{ name: 'She said "hello"', age: 30, city: 'NYC' }];
    exportToCSV(data, columns, 'test');

    const csvContent = createdUrl.content;
    expect(csvContent).toContain('"She said ""hello"""');
  });

  it('should escape newlines in values', () => {
    const data = [{ name: 'Line1\nLine2', age: 30, city: 'NYC' }];
    exportToCSV(data, columns, 'test');

    const csvContent = createdUrl.content;
    expect(csvContent).toContain('"Line1\nLine2"');
  });

  it('should handle numeric values without escaping', () => {
    const data = [{ name: 'Alice', age: 30, city: 'NYC' }];
    exportToCSV(data, columns, 'test');

    const csvContent = createdUrl.content;
    const lines = csvContent.split('\n');
    const dataLine = lines[1];
    expect(dataLine).toBe('Alice,30,NYC');
  });

  it('should include BOM for UTF-8 encoding', () => {
    const data = [{ name: 'שלום', age: 1, city: 'ירושלים' }];
    exportToCSV(data, columns, 'test');

    const csvContent = createdUrl.content;
    expect(csvContent.startsWith('\uFEFF')).toBe(true);
  });

  it('should handle single column', () => {
    const singleCol = [{ title: 'ID', dataIndex: 'id' }];
    const data = [{ id: 1 }, { id: 2 }];
    exportToCSV(data, singleCol, 'ids');

    const csvContent = createdUrl.content;
    expect(csvContent).toContain('ID\n1\n2');
  });

  it('should set correct blob type', () => {
    const data = [{ name: 'Alice', age: 30, city: 'NYC' }];
    exportToCSV(data, columns, 'test');

    expect(createdUrl.options.type).toBe('text/csv;charset=utf-8;');
  });

  it('should not add double .csv extension when filename already ends with .csv', () => {
    const data = [{ name: 'Alice', age: 30, city: 'NYC' }];
    exportToCSV(data, columns, 'users.csv');

    expect(clickedLink.download).toBe('users.csv');
    expect(clickedLink.download).not.toBe('users.csv.csv');
  });
});

describe('exportToExcel', () => {
  let clickedLink;
  let createdUrl;

  beforeEach(() => {
    clickedLink = null;
    createdUrl = null;

    vi.stubGlobal('URL', {
      createObjectURL: blob => {
        createdUrl = blob;
        return 'blob:mock-url';
      },
      revokeObjectURL: () => {},
    });

    vi.stubGlobal('document', {
      createElement: (_tag) => {
        const el = { href: '', download: '', click: () => { clickedLink = el; } };
        return el;
      },
    });

    vi.stubGlobal('Blob', class MockBlob {
      constructor(parts, options) {
        this.parts = parts;
        this.options = options;
        this.content = parts.join('');
      }
    });
  });

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
  ];

  it('should not export when data is null', () => {
    exportToExcel(null, columns, 'test');
    expect(clickedLink).toBeNull();
  });

  it('should not export when data is empty array', () => {
    exportToExcel([], columns, 'test');
    expect(clickedLink).toBeNull();
  });

  it('should export data as Excel HTML with correct structure', () => {
    const data = [{ name: 'Alice', age: 30 }, { name: 'Bob', age: 25 }];
    exportToExcel(data, columns, 'users');

    expect(clickedLink).not.toBeNull();
    expect(clickedLink.download).toBe('users.xls');
    expect(createdUrl.content).toContain('<table');
    expect(createdUrl.content).toContain('<th>Name</th>');
    expect(createdUrl.content).toContain('<th>Age</th>');
    expect(createdUrl.content).toContain('<td>Alice</td>');
    expect(createdUrl.content).toContain('<td>30</td>');
    expect(createdUrl.options.type).toBe('application/vnd.ms-excel;charset=utf-8;');
  });

  it('should escape HTML in values', () => {
    const data = [{ name: '<script>alert(1)</script>', age: 1 }];
    exportToExcel(data, columns, 'test');

    expect(createdUrl.content).toContain('&lt;script&gt;');
  });

  it('should not add double .xls extension when filename already ends with .xls', () => {
    const data = [{ name: 'Alice', age: 30 }];
    exportToExcel(data, columns, 'report.xls');

    expect(clickedLink.download).toBe('report.xls');
  });
});

describe('exportToPDF', () => {
  let openedWindow;
  let writtenContent;
  let openSpy;

  beforeEach(() => {
    openedWindow = null;
    writtenContent = null;
    const mockWin = {
      document: {
        write: html => { writtenContent = html; },
        close: vi.fn(),
      },
      focus: vi.fn(),
      print: vi.fn(),
      close: vi.fn(),
    };
    openSpy = vi.spyOn(window, 'open').mockImplementation(() => {
      openedWindow = mockWin;
      return mockWin;
    });
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    openSpy?.mockRestore();
  });

  const columns = [
    { title: 'Name', dataIndex: 'name' },
    { title: 'Age', dataIndex: 'age' },
  ];

  it('should not export when data is null', () => {
    exportToPDF(null, columns, 'test');
    expect(openedWindow).toBeNull();
  });

  it('should not export when data is empty array', () => {
    exportToPDF([], columns, 'test');
    expect(openedWindow).toBeNull();
  });

  it('should open new window with HTML table and trigger print', () => {
    const data = [{ name: 'Alice', age: 30 }];
    exportToPDF(data, columns, 'report', 'דוח משתמשים');

    expect(openedWindow).not.toBeNull();
    expect(writtenContent).toContain('<table');
    expect(writtenContent).toContain('דוח משתמשים');
    expect(writtenContent).toContain('<th>Name</th>');
    expect(writtenContent).toContain('<td>Alice</td>');

    vi.advanceTimersByTime(300);
    expect(openedWindow.print).toHaveBeenCalled();
    expect(openedWindow.close).toHaveBeenCalled();
  });

  it('should use default title when not provided', () => {
    const data = [{ name: 'Alice', age: 30 }];
    exportToPDF(data, columns, 'report');

    expect(writtenContent).toContain('ייצוא');
  });
});
