import React, { useState, useRef } from 'react';
import { Plus, Merge, Split, Trash2, RotateCcw, Eye } from 'lucide-react';

interface Cell {
  content: string;
  rowspan: number;
  colspan: number;
  isHeader: boolean;
}

interface SelectedCell {
  row: number;
  col: number;
}

interface StartCell {
  row: number;
  col: number;
}

const TableEditor: React.FC = () => {
  // 초기 테이블 데이터
  const [tableData, setTableData] = useState<(Cell | null)[][]>([
    [
      { content: 'Header 1', rowspan: 1, colspan: 1, isHeader: true },
      { content: 'Header 2', rowspan: 1, colspan: 1, isHeader: true },
      { content: 'Header 3', rowspan: 1, colspan: 1, isHeader: true }
    ],
    [
      { content: 'Cell 1', rowspan: 1, colspan: 1, isHeader: false },
      { content: 'Cell 2', rowspan: 1, colspan: 1, isHeader: false },
      { content: 'Cell 3', rowspan: 1, colspan: 1, isHeader: false }
    ],
    [
      { content: 'Cell 4', rowspan: 1, colspan: 1, isHeader: false },
      { content: 'Cell 5', rowspan: 1, colspan: 1, isHeader: false },
      { content: 'Cell 6', rowspan: 1, colspan: 1, isHeader: false }
    ]
  ]);

  const [selectedCells, setSelectedCells] = useState<SelectedCell[]>([]);
  const [isSelecting, setIsSelecting] = useState<boolean>(false);
  const [showDataModal, setShowDataModal] = useState<boolean>(false);
  const [showHtml, setShowHtml] = useState<boolean>(false);
  const startCell = useRef<StartCell | null>(null);

  // 행 추가
  const addRow = () => {
    const cols = tableData[0]?.length || 3;
    const newRow = Array(cols)
      .fill(null)
      .map((_, i) => ({
        content: `New Cell`,
        rowspan: 1,
        colspan: 1,
        isHeader: false
      }));

    if (selectedCells.length === 1) {
      const selectedRow = selectedCells[0].row;
      const newTableData = [
        ...tableData.slice(0, selectedRow + 1),
        newRow,
        ...tableData.slice(selectedRow + 1)
      ];
      setTableData(newTableData);
    } else {
      setTableData([...tableData, newRow]);
    }
  };

  // 열 추가
  const addColumn = () => {
    let newTableData;
    if (selectedCells.length === 1) {
      const selectedCol = selectedCells[0].col;
      newTableData = tableData.map(row => {
        const newCell = {
          content: `New Cell`,
          rowspan: 1,
          colspan: 1,
          isHeader: false
        };
        const newRowData = [...row];
        newRowData.splice(selectedCol + 1, 0, newCell);
        return newRowData;
      });
    } else {
      newTableData = tableData.map(row => [
        ...row,
        {
          content: `New Cell`,
          rowspan: 1,
          colspan: 1,
          isHeader: false
        }
      ]);
    }
    setTableData(newTableData);
  };

  // 행 삭제
  const deleteRow = (rowIndex: number): void => {
    if (tableData.length > 1) {
      const newTableData = tableData.filter((_, index) => index !== rowIndex);
      setTableData(newTableData);
    }
  };

  // 열 삭제
  const deleteColumn = (colIndex: number): void => {
    if (tableData[0]?.length > 1) {
      const newTableData = tableData.map(row =>
        row.filter((_, index) => index !== colIndex)
      );
      setTableData(newTableData);
    }
  };

  // 셀 선택 시작
  const handleMouseDown = (rowIndex: number, colIndex: number): void => {
    setIsSelecting(true);
    startCell.current = { row: rowIndex, col: colIndex };
    setSelectedCells([{ row: rowIndex, col: colIndex }]);
  };

  // 셀 선택 중
  const handleMouseEnter = (rowIndex: number, colIndex: number): void => {
    if (isSelecting && startCell.current) {
      const minRow = Math.min(startCell.current.row, rowIndex);
      const maxRow = Math.max(startCell.current.row, rowIndex);
      const minCol = Math.min(startCell.current.col, colIndex);
      const maxCol = Math.max(startCell.current.col, colIndex);

      const selected: SelectedCell[] = [];
      for (let r = minRow; r <= maxRow; r++) {
        for (let c = minCol; c <= maxCol; c++) {
          selected.push({ row: r, col: c });
        }
      }
      setSelectedCells(selected);
    }
  };

  // 셀 선택 종료
  const handleMouseUp = (): void => {
    setIsSelecting(false);
  };

  // 셀이 선택되어 있는지 확인
  const isCellSelected = (rowIndex: number, colIndex: number): boolean => {
    return selectedCells.some(cell => cell.row === rowIndex && cell.col === colIndex);
  };

  // 셀 병합
  const mergeCells = (): void => {
    if (selectedCells.length < 2) return;

    const minRow = Math.min(...selectedCells.map(c => c.row));
    const maxRow = Math.max(...selectedCells.map(c => c.row));
    const minCol = Math.min(...selectedCells.map(c => c.col));
    const maxCol = Math.max(...selectedCells.map(c => c.col));

    const newTableData = [...tableData];

    // 병합될 셀들의 내용을 합치기
    const mergedContent = selectedCells
      .map(cell => newTableData[cell.row][cell.col]?.content)
      .filter((content): content is string => Boolean(content && content.trim()))
      .join(' ');

    // 첫 번째 셀에 병합 정보 설정
    const firstCell = newTableData[minRow][minCol];
    if (firstCell) {
      newTableData[minRow][minCol] = {
        ...firstCell,
        content: mergedContent || 'Merged Cell',
        rowspan: maxRow - minRow + 1,
        colspan: maxCol - minCol + 1
      };
    }

    // 나머지 셀들은 null로 설정 (렌더링하지 않음)
    selectedCells.forEach(cell => {
      if (cell.row !== minRow || cell.col !== minCol) {
        newTableData[cell.row][cell.col] = null;
      }
    });

    setTableData(newTableData);
    setSelectedCells([]);
  };

  // 셀 분할
  const splitCells = (): void => {
    if (selectedCells.length !== 1) return;

    const cell = selectedCells[0];
    const currentCell = tableData[cell.row][cell.col];

    if (!currentCell || (currentCell.rowspan === 1 && currentCell.colspan === 1)) return;

    const newTableData = [...tableData];

    // 분할된 셀들 생성
    for (let r = 0; r < currentCell.rowspan; r++) {
      for (let c = 0; c < currentCell.colspan; c++) {
        const newRow = cell.row + r;
        const newCol = cell.col + c;

        newTableData[newRow][newCol] = {
          content: r === 0 && c === 0 ? currentCell.content : 'Split Cell',
          rowspan: 1,
          colspan: 1,
          isHeader: currentCell.isHeader
        };
      }
    }

    setTableData(newTableData);
    setSelectedCells([]);
  };

  // 셀 내용 수정
  const updateCellContent = (rowIndex: number, colIndex: number, content: string): void => {
    const newTableData = [...tableData];
    const targetCell = newTableData[rowIndex][colIndex];
    if (targetCell) {
      targetCell.content = content;
      setTableData(newTableData);
    }
  };

  // 테이블 초기화
  const resetTable = (): void => {
    setTableData([
      [
        { content: 'Header 1', rowspan: 1, colspan: 1, isHeader: true },
        { content: 'Header 2', rowspan: 1, colspan: 1, isHeader: true },
        { content: 'Header 3', rowspan: 1, colspan: 1, isHeader: true }
      ],
      [
        { content: 'Cell 1', rowspan: 1, colspan: 1, isHeader: false },
        { content: 'Cell 2', rowspan: 1, colspan: 1, isHeader: false },
        { content: 'Cell 3', rowspan: 1, colspan: 1, isHeader: false }
      ]
    ]);
    setSelectedCells([]);
  };

  // HTML 테이블 생성
  const generateHTMLTable = (): string => {
    let html = '<table border="1" style="border-collapse: collapse;">\n';

    tableData.forEach((row, rowIndex) => {
      html += '  <tr>\n';
      row.forEach((cell, colIndex) => {
        if (cell) {
          const tag = cell.isHeader ? 'th' : 'td';
          let attributes = '';
          if (cell.rowspan > 1) attributes += ` rowspan="${cell.rowspan}"`;
          if (cell.colspan > 1) attributes += ` colspan="${cell.colspan}"`;

          html += `    <${tag}${attributes}>${cell.content}</${tag}>\n`;
        }
      });
      html += '  </tr>\n';
    });

    html += '</table>';
    return html;
  };

  return (
    <div className="p-6 max-w-6xl mx-auto bg-white">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">테이블 편집기</h1>

      {/* 컨트롤 패널 */}
      <div className="mb-6 flex flex-wrap gap-3 w-full justify-between">
        <div className="flex flex-wrap gap-3">
          <button
            onClick={addRow}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            <Plus size={16} />
            행 추가
          </button>

          <button
            onClick={addColumn}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
          >
            <Plus size={16} />
            열 추가
          </button>

          <button
            onClick={mergeCells}
            disabled={selectedCells.length < 2}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Merge size={16} />
            셀 병합
          </button>

          <button
            onClick={splitCells}
            disabled={selectedCells.length !== 1}
            className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Split size={16} />
            셀 분할
          </button>

          <button
            onClick={resetTable}
            className="flex items-center gap-2 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            <RotateCcw size={16} />
            초기화
          </button>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => setShowDataModal(!showDataModal)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 transition-colors"
          >
            <Eye size={16} />
            {showDataModal ? '데이터 숨기기' : '데이터 보기'}
          </button>

          <button
            onClick={() => setShowHtml(!showHtml)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 transition-colors"
          >
            <Eye size={16} />
            {showHtml ? 'HTML 숨기기' : 'HTML 보기'}
          </button>
        </div>
      </div>

      {/* 선택된 셀 정보 */}
      {selectedCells.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-700">
            선택된 셀: {selectedCells.length}개
            {selectedCells.length > 1 && " (드래그로 범위 선택)"}
          </p>
        </div>
      )}

      {/* 테이블 편집 영역 */}
      <div className="mb-6 overflow-x-auto">
        <table
          className="border-2 border-gray-300 border-collapse"
          onMouseUp={handleMouseUp}
        >
          <tbody>
            {tableData.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {/* 행 삭제 버튼 */}
                <td className="bg-gray-100 p-1 border border-gray-300">
                  <button
                    onClick={() => deleteRow(rowIndex)}
                    className="text-red-500 hover:text-red-700 p-1"
                    title="행 삭제"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>

                {row.map((cell, colIndex) => {
                  if (!cell) return null;

                  const isSelected = isCellSelected(rowIndex, colIndex);
                  const cellClass = `
                    border border-gray-300 p-2 min-w-24 text-center cursor-pointer
                    ${cell.isHeader ? 'bg-gray-200 font-semibold' : 'bg-white'}
                    ${isSelected ? 'bg-yellow-200 border-yellow-500 border-2' : 'hover:bg-gray-50'}
                    transition-colors
                  `;

                  return (
                    <td
                      key={colIndex}
                      className={cellClass}
                      rowSpan={cell.rowspan}
                      colSpan={cell.colspan}
                      onMouseDown={() => handleMouseDown(rowIndex, colIndex)}
                      onMouseEnter={() => handleMouseEnter(rowIndex, colIndex)}
                    >
                      <input
                        type="text"
                        value={cell.content}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateCellContent(rowIndex, colIndex, e.target.value)}
                        className={`w-full border-none outline-none text-center ${isSelected ? 'bg-yellow-300 text-black placeholder-yellow-500' : 'bg-transparent'
                          }`}
                        onClick={(e: React.MouseEvent<HTMLInputElement>) => e.stopPropagation()}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}

            {/* 열 삭제 버튼 행 */}
            <tr>
              <td className="bg-gray-100 p-1 border border-gray-300"></td>
              {tableData[0]?.map((_, colIndex) => (
                <td key={colIndex} className="bg-gray-100 p-1 border border-gray-300 text-center">
                  <button
                    onClick={() => deleteColumn(colIndex)}
                    className="text-red-500 hover:text-red-700 p-1"
                    title="열 삭제"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* 사용법 안내 */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="font-semibold mb-2">사용법:</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• 셀을 클릭하거나 드래그해서 선택</li>
          <li>• <strong>행/열 추가:</strong> 단일 셀 선택 후 버튼을 클릭하면 선택한 셀의 다음 위치에 행/열이 추가됩니다. 선택하지 않으면 마지막에 추가됩니다.</li>
          <li>• <strong>셀 병합:</strong> 2개 이상 셀 선택 후 "셀 병합" 클릭</li>
          <li>• <strong>셀 분할:</strong> 병합된 셀 선택 후 "셀 분할" 클릭</li>
          <li>• 셀 내용은 직접 클릭해서 수정 가능</li>
          <li>• 휴지통 아이콘으로 행/열 삭제</li>
        </ul>
      </div>

      {/* HTML 코드 생성 */}
      {showHtml && (
        <div className="border-2 border-gray-200 rounded-lg">
          <div className="bg-gray-100 p-3 border-b border-gray-200 flex justify-between items-center">
            <h3 className="font-semibold">생성된 HTML 코드:</h3>
            <button
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(generateHTMLTable());
                  alert('HTML 코드가 클립보드에 복사되었습니다!');
                } catch (error) {
                  console.error('클립보드 복사 실패:', error);
                  alert('클립보드 복사에 실패했습니다.');
                }
              }}
              className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
            >
              📋 복사
            </button>
          </div>
          <div className="p-4">
            <pre className="bg-gray-50 p-4 rounded text-sm overflow-x-auto">
              <code>{generateHTMLTable()}</code>
            </pre>
          </div>
        </div>
      )}

      {/* 데이터 보기 모달 */}
      {showDataModal && (
        <div className="border-2 border-gray-200 rounded-lg">
          <div className="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">현재 테이블 데이터 (JSON)</h3>
              <div className="flex gap-2">
                <button
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(JSON.stringify(tableData, null, 2));
                      alert('JSON 데이터가 클립보드에 복사되었습니다!');
                    } catch (error) {
                      console.error('클립보드 복사 실패:', error);
                      alert('클립보드 복사에 실패했습니다.');
                    }
                  }}
                  className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 transition-colors"
                >
                  📋 JSON 복사
                </button>
                <button
                  onClick={() => setShowDataModal(false)}
                  className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
                >
                  ✕ 닫기
                </button>
              </div>
            </div>
            <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto max-h-96">
              <code>{JSON.stringify(tableData, null, 2)}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default TableEditor;