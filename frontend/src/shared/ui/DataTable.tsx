import { Download as DownloadIcon } from '@mui/icons-material';
import { Box, LinearProgress, Button } from '@mui/material';
import {
  DataGrid,
  GridColDef,
  GridPaginationModel,
  GridRowSelectionModel,
  GridSortModel,
  ruRU,
  enUS,
} from '@mui/x-data-grid';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

interface DataTableProps<T> {
  rows: T[];
  columns: GridColDef[];
  rowCount: number;
  loading?: boolean;
  paginationModel: GridPaginationModel;
  onPaginationModelChange: (model: GridPaginationModel) => void;
  sortModel?: GridSortModel;
  onSortModelChange?: (model: GridSortModel) => void;
  checkboxSelection?: boolean;
  rowSelectionModel?: GridRowSelectionModel;
  onRowSelectionModelChange?: (model: GridRowSelectionModel) => void;
  exportFileName?: string;
}

export const DataTable = <T extends { id: string | number }>({
  rows,
  columns,
  rowCount,
  loading = false,
  paginationModel,
  onPaginationModelChange,
  sortModel,
  onSortModelChange,
  checkboxSelection = false,
  rowSelectionModel,
  onRowSelectionModelChange,
  exportFileName = 'export',
}: DataTableProps<T>) => {
  const { i18n } = useTranslation();

  const handleExportCSV = useCallback(() => {
    const exportCols = columns.filter((c) => c.field !== 'actions' && c.field !== '__check__');
    const headers = exportCols.map((col) => col.headerName || col.field).join(';');
    const csvRows = rows.map((row) =>
      exportCols
        .map((col) => {
          const val = (row as Record<string, unknown>)[col.field];
          if (Array.isArray(val))
            return val
              .map((v) =>
                typeof v === 'object' && v !== null
                  ? ((v as Record<string, unknown>)['name'] ?? '')
                  : v
              )
              .join(', ');
          return String(val ?? '').replace(/;/g, ',');
        })
        .join(';')
    );

    const csvContent = [headers, ...csvRows].join('\r\n');
    const bom = new Uint8Array([0xef, 0xbb, 0xbf]);
    const blob = new Blob([bom, csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${exportFileName}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [rows, columns, exportFileName]);

  const localeText =
    i18n.language === 'ru'
      ? ruRU.components.MuiDataGrid.defaultProps.localeText
      : enUS.components.MuiDataGrid.defaultProps.localeText;

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
        <Button
          size="small"
          variant="outlined"
          startIcon={<DownloadIcon />}
          onClick={handleExportCSV}
        >
          {i18n.language === 'ru' ? 'Скачать CSV' : 'Download CSV'}
        </Button>
      </Box>
      <DataGrid
        rows={rows}
        columns={columns}
        rowCount={rowCount}
        loading={loading}
        paginationMode="server"
        paginationModel={paginationModel}
        onPaginationModelChange={onPaginationModelChange}
        sortModel={sortModel}
        onSortModelChange={onSortModelChange}
        pageSizeOptions={[5, 10, 25, 50]}
        checkboxSelection={checkboxSelection}
        rowSelectionModel={rowSelectionModel}
        onRowSelectionModelChange={onRowSelectionModelChange}
        disableRowSelectionOnClick
        disableColumnFilter
        disableColumnSelector
        disableDensitySelector
        disableColumnMenu
        autoHeight
        slots={{ loadingOverlay: LinearProgress }}
        localeText={localeText}
        sx={{
          border: 'none',
          '& .MuiDataGrid-cell': {
            border: 'none',
          },
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: 'rgba(0, 0, 0, 0.04)',
          },
        }}
      />
    </Box>
  );
};
