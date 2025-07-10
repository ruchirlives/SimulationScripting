import { setupFileUpload, updateFileInfo } from './file_upload.js';
import { setupEditorPersistence, restoreEditorsFromStorage, setupDownloadButtons } from './editor_persistence.js';
import { setupFormSubmission } from './form_submission.js';
import { showTab } from './tab_handling.js';

// Main entry point for page scripts
window.addEventListener('DOMContentLoaded', () => {
  setupFileUpload();
  restoreEditorsFromStorage();
  setupEditorPersistence();
  setupDownloadButtons();
  setupFormSubmission();
});

// Expose updateFileInfo for file_upload.js usage
window.updateFileInfo = updateFileInfo;
window.showTab = showTab;
