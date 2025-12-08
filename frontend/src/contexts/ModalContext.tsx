import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import Modal, { ModalType } from '@/components/common/Modal';

interface ModalOptions {
    message: string;
    title?: string;
    type?: ModalType;
    confirmText?: string;
    cancelText?: string;
    showCancel?: boolean;
    onConfirm?: () => void;
}

interface ModalContextType {
    showModal: (options: ModalOptions) => void;
    showInfo: (message: string, title?: string) => void;
    showSuccess: (message: string, title?: string) => void;
    showWarning: (message: string, title?: string) => void;
    showError: (message: string, title?: string) => void;
    showConfirm: (message: string, onConfirm: () => void, title?: string) => void;
    closeModal: () => void;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

interface ModalState {
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

export function ModalProvider({ children }: { children: ReactNode }) {
    const [modalState, setModalState] = useState<ModalState>(initialState);

    const showModal = useCallback((options: ModalOptions) => {
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
    }, []);

    const closeModal = useCallback(() => {
        setModalState((prev) => ({ ...prev, isOpen: false }));
    }, []);

    const handleConfirm = useCallback(() => {
        if (modalState.onConfirmCallback) {
            modalState.onConfirmCallback();
        }
        closeModal();
    }, [modalState.onConfirmCallback, closeModal]);

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

    return (
        <ModalContext.Provider
            value={{
                showModal,
                showInfo,
                showSuccess,
                showWarning,
                showError,
                showConfirm,
                closeModal,
            }}
        >
            {children}
            <Modal
                isOpen={modalState.isOpen}
                onClose={closeModal}
                onConfirm={handleConfirm}
                title={modalState.title}
                message={modalState.message}
                type={modalState.type}
                confirmText={modalState.confirmText}
                cancelText={modalState.cancelText}
                showCancel={modalState.showCancel}
            />
        </ModalContext.Provider>
    );
}

export function useGlobalModal() {
    const context = useContext(ModalContext);
    if (!context) {
        throw new Error('useGlobalModal must be used within a ModalProvider');
    }
    return context;
}
