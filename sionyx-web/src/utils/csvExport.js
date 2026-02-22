export const exportToCSV = (data, columns, filename) => {
  if (!data || data.length === 0) return;

  const headers = columns.map(c => c.title).join(',');
  const rows = data.map(row =>
    columns
      .map(c => {
        let val = row[c.dataIndex] ?? '';
        if (typeof val === 'string' && (val.includes(',') || val.includes('"') || val.includes('\n'))) {
          val = `"${val.replace(/"/g, '""')}"`;
        }
        return val;
      })
      .join(',')
  );

  const bom = '\uFEFF';
  const csv = bom + [headers, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.csv`;
  link.click();
  URL.revokeObjectURL(url);
};
