import { useState, useCallback } from 'react';
import type { ModalType } from '@/components/common/Modal';

export interface ModalState {
    isOpen: boolean;
    message: string;
    title?: string;
    type: ModalType;
    showCancel: boolean;
    confirmText: string;
    cancelText: string;
    onConfirmCallback?: () => void;
}

const initialState: ModalState = {
    isOpen: false,
    message: '',
    title: undefined,
    type: 'info',
    showCancel: false,
    confirmText: 'OK',
    cancelText: 'キャンセル',
    onConfirmCallback: undefined,
};

export function useModal() {
    const [modalState, setModalState] = useState<ModalState>(initialState);

    const showModal = useCallback(
        (options: {
            message: string;
            title?: string;
            type?: ModalType;
            confirmText?: string;
            cancelText?: string;
            showCancel?: boolean;
            onConfirm?: () => void;
        }) => {
            setModalState({
                isOpen: true,
                message: options.message,
                title: options.title,
                type: options.type || 'info',
                showCancel: options.showCancel ?? false,
                confirmText: options.confirmText || 'OK',
                cancelText: options.cancelText || 'キャンセル',
                onConfirmCallback: options.onConfirm,
            });
        },
        []
    );

    const closeModal = useCallback(() => {
        setModalState((prev) => ({ ...prev, isOpen: false }));
    }, []);

    const handleConfirm = useCallback(() => {
        if (modalState.onConfirmCallback) {
            modalState.onConfirmCallback();
        }
    }, [modalState.onConfirmCallback]);

    // 便利なショートカットメソッド
    const showInfo = useCallback(
        (message: string, title?: string) => {
            showModal({ message, title, type: 'info' });
        },
        [showModal]
    );

    const showSuccess = useCallback(
        (message: string, title?: string) => {
            showModal({ message, title, type: 'success' });
        },
        [showModal]
    );

    const showWarning = useCallback(
        (message: string, title?: string) => {
            showModal({ message, title, type: 'warning' });
        },
        [showModal]
    );

    const showError = useCallback(
        (message: string, title?: string) => {
            showModal({ message, title, type: 'error' });
        },
        [showModal]
    );

    const showConfirm = useCallback(
        (message: string, onConfirm: () => void, title?: string) => {
            showModal({
                message,
                title: title || '確認',
                type: 'confirm',
                showCancel: true,
                confirmText: '確認',
                onConfirm,
            });
        },
        [showModal]
    );

    return {
        modalState,
        showModal,
        closeModal,
        handleConfirm,
        showInfo,
        showSuccess,
        showWarning,
        showError,
        showConfirm,
    };
}
