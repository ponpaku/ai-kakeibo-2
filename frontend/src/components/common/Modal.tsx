import { useEffect, useCallback } from 'react';
import { X, CheckCircle, AlertTriangle, Info, AlertCircle } from 'lucide-react';

export type ModalType = 'info' | 'success' | 'warning' | 'error' | 'confirm';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm?: () => void;
    title?: string;
    message: string;
    type?: ModalType;
    confirmText?: string;
    cancelText?: string;
    showCancel?: boolean;
}

const iconMap = {
    info: { Icon: Info, color: 'text-blue-500', bgColor: 'bg-blue-100' },
    success: { Icon: CheckCircle, color: 'text-green-500', bgColor: 'bg-green-100' },
    warning: { Icon: AlertTriangle, color: 'text-yellow-500', bgColor: 'bg-yellow-100' },
    error: { Icon: AlertCircle, color: 'text-red-500', bgColor: 'bg-red-100' },
    confirm: { Icon: AlertTriangle, color: 'text-orange-500', bgColor: 'bg-orange-100' },
};

export default function Modal({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    type = 'info',
    confirmText = 'OK',
    cancelText = 'キャンセル',
    showCancel = false,
}: ModalProps) {
    const { Icon, color, bgColor } = iconMap[type];

    // ESCキーでモーダルを閉じる
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        },
        [onClose]
    );

    useEffect(() => {
        if (isOpen) {
            document.addEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'hidden';
        }

        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, handleKeyDown]);

    if (!isOpen) return null;

    const handleConfirm = () => {
        if (onConfirm) {
            onConfirm();
        }
        onClose();
    };

    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4 animate-fadeIn"
            onClick={handleBackdropClick}
        >
            <div
                className="bg-white rounded-xl shadow-2xl max-w-md w-full transform transition-all duration-200 ease-out animate-scaleIn"
                onClick={(e) => e.stopPropagation()}
            >
                {/* ヘッダー */}
                <div className="flex items-center justify-between p-4 border-b border-gray-100">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${bgColor}`}>
                            <Icon className={color} size={20} />
                        </div>
                        {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 rounded-full hover:bg-gray-100 transition-colors"
                        aria-label="閉じる"
                    >
                        <X className="text-gray-500" size={20} />
                    </button>
                </div>

                {/* コンテンツ */}
                <div className="p-6">
                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{message}</p>
                </div>

                {/* フッター（ボタン） */}
                <div className="flex gap-3 p-4 border-t border-gray-100 bg-gray-50 rounded-b-xl">
                    {showCancel && (
                        <button
                            onClick={onClose}
                            className="flex-1 px-4 py-2.5 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
                        >
                            {cancelText}
                        </button>
                    )}
                    <button
                        onClick={handleConfirm}
                        className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors ${type === 'error'
                                ? 'bg-red-600 text-white hover:bg-red-700'
                                : type === 'warning' || type === 'confirm'
                                    ? 'bg-orange-600 text-white hover:bg-orange-700'
                                    : type === 'success'
                                        ? 'bg-green-600 text-white hover:bg-green-700'
                                        : 'bg-primary-600 text-white hover:bg-primary-700'
                            }`}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
}
