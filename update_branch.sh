#!/bin/bash

# Mevcut değişiklikleri stash et
git stash

# Tüm branch'leri fetch et
git fetch upstream

# update/1 branch'ini kontrol et
if git show-ref --verify --quiet refs/remotes/upstream/update/1; then
    echo "update/1 branch bulundu, checkout ediliyor..."
    git checkout -b update/1 upstream/update/1
else
    echo "update/1 branch bulunamadı"
    echo "Mevcut branch'ler:"
    git branch -r
fi

# Stash'ten değişiklikleri geri al
git stash pop 