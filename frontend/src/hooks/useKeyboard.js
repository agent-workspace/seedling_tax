import { useEffect, useState, useCallback } from 'react';

export default function useKeyboard({ onAltKey, onNumberKey, onEscape, onEnter } = {}) {
  const [showShortcuts, setShowShortcuts] = useState(false);

  const handler = useCallback(
    (e) => {
      const target = e.target;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable;

      // Alt + key for module switching
      if (e.altKey && !e.ctrlKey && !e.metaKey) {
        const key = e.key.toLowerCase();
        if ('dievtrs'.includes(key) && key.length === 1) {
          e.preventDefault();
          if (onAltKey) onAltKey(key);
          return;
        }
      }

      // Number keys 1-9 for sidebar (only when not in input)
      if (!isInput && !e.altKey && !e.ctrlKey && !e.metaKey) {
        const num = parseInt(e.key, 10);
        if (num >= 1 && num <= 9) {
          e.preventDefault();
          if (onNumberKey) onNumberKey(num);
          return;
        }

        // ? for shortcuts overlay
        if (e.key === '?') {
          e.preventDefault();
          setShowShortcuts((prev) => !prev);
          return;
        }

        // N for "new" action
        if (e.key.toLowerCase() === 'n' && !isInput) {
          // handled by pages individually
        }
      }

      // Escape
      if (e.key === 'Escape') {
        if (showShortcuts) {
          setShowShortcuts(false);
          return;
        }
        if (onEscape) onEscape();
        return;
      }

      // Enter to submit (handled natively by forms, but allow custom handler)
      if (e.key === 'Enter' && !isInput && onEnter) {
        onEnter();
      }
    },
    [onAltKey, onNumberKey, onEscape, onEnter, showShortcuts]
  );

  useEffect(() => {
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handler]);

  return { showShortcuts, setShowShortcuts };
}
