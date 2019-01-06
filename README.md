# johnny_bootstrap
A helper script for organizing existing files into the Johnny Decimal system.

The input to the script is an emacs org-mode file which is both read and written by the script. The user can assign categories to each 
file or directory and tell say what the script should do with it. A sample org-mode file is provided.

How to use:

Put the following in your .emacs file to cause F5 to run the script and update the contents of the table, edit the paths to match:

```
(defun johnny-organize-buffer ()
  "Asks for a command and executes it in inferior shell with current buffer
as input."
  (interactive)
  (save-buffer)
  (let ((line (line-number-at-pos))
	(col  (current-column)))
    (shell-command-on-region
     (point-min) (point-max)
     "python \"C:\\path\\to\\python\\script\\johnny_bootstrap.py\" \"C:\\path\\to\\organize-files.org\"")
    (revert-buffer t t)
    (org-table-recalculate-buffer-tables)
    (outline-show-all)
    (with-no-warnings (goto-line line))
    (move-to-column col)
  ))


(global-set-key (kbd "<f5>") 'johnny-organize-buffer)

(global-hl-line-mode 1)
```

Restart emacs, then open organize-files.org. Set the sourcedir and targetdir properties to the location of the current files and the location of the reorganized files. Press F5.

Keep editing the table and pressing F5 until you are satisfied with the categories.

Do a dry-run of the script from a command line:

    python johnny_bootstrap.py organize_files.org --copy
   
When satisfied, run the actual copy:
  
    python johnny_bootstrap.py organize_files.org --copy --no-dry-run
   
This does not touch the original files but simply makes a copy into the new location. Regardless, use at your own risk and make sure yoy have backups.
