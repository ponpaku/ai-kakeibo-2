import { useState } from 'react';
import { Delete } from 'lucide-react';

interface CalculatorProps {
  onCalculate: (value: number) => void;
}

export default function Calculator({ onCalculate }: CalculatorProps) {
  const [display, setDisplay] = useState('0');
  const [previousValue, setPreviousValue] = useState<number | null>(null);
  const [operation, setOperation] = useState<string | null>(null);

  const handleNumber = (num: string) => {
    setDisplay((prev) => (prev === '0' ? num : prev + num));
  };

  const handleOperation = (op: string) => {
    const currentValue = parseFloat(display);
    if (previousValue !== null && operation) {
      calculate();
    } else {
      setPreviousValue(currentValue);
    }
    setOperation(op);
    setDisplay('0');
  };

  const calculate = () => {
    const currentValue = parseFloat(display);
    let result = 0;

    if (previousValue !== null && operation) {
      switch (operation) {
        case '+':
          result = previousValue + currentValue;
          break;
        case '-':
          result = previousValue - currentValue;
          break;
        case '*':
          result = previousValue * currentValue;
          break;
        case '/':
          result = previousValue / currentValue;
          break;
      }
      setDisplay(result.toString());
      setPreviousValue(null);
      setOperation(null);
    }
  };

  const clear = () => {
    setDisplay('0');
    setPreviousValue(null);
    setOperation(null);
  };

  const handleConfirm = () => {
    const value = parseFloat(display);
    if (!isNaN(value)) {
      onCalculate(value);
    }
  };

  const buttons = [
    ['7', '8', '9', '/'],
    ['4', '5', '6', '*'],
    ['1', '2', '3', '-'],
    ['0', '.', '=', '+'],
  ];

  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <div className="mb-4">
        <div className="bg-gray-100 p-4 rounded-lg text-right text-2xl font-mono">
          {display}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 mb-4">
        {buttons.map((row, i) => (
          row.map((btn) => (
            <button
              key={`${i}-${btn}`}
              onClick={() => {
                if (btn === '=') {
                  calculate();
                } else if (['+', '-', '*', '/'].includes(btn)) {
                  handleOperation(btn);
                } else {
                  handleNumber(btn);
                }
              }}
              className={`p-4 rounded-lg font-semibold text-lg transition-colors ${
                ['+', '-', '*', '/'].includes(btn)
                  ? 'bg-primary-500 text-white hover:bg-primary-600'
                  : btn === '='
                  ? 'bg-green-500 text-white hover:bg-green-600'
                  : 'bg-gray-200 text-gray-900 hover:bg-gray-300'
              }`}
            >
              {btn}
            </button>
          ))
        ))}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={clear}
          className="flex items-center justify-center gap-2 p-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          <Delete size={20} />
          クリア
        </button>
        <button
          onClick={handleConfirm}
          className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-semibold"
        >
          この金額を使用
        </button>
      </div>
    </div>
  );
}
