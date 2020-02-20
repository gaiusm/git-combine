# git-combine

git-combine is a program which combines two git repositories.  It
effectively performs: 'des += inc' given two repositories des and inc.
git-combine effectively allows you to perform a rebase of repository
with another repository.

git-combine generates a patch set of shell scripts one for every
commit in the inc repository which will be applied to the des
repository.  It can be configured to adjust the relative position of
the inc repository tree onto the des repository tree.  git-combine
is configured using a .comb script.