cut -f1 -d= t80s.txt | gsed 's/T80S/OAJ/g;s/ *$//' | sort > l1
cut -f1 -d= cefca.txt | gsed 's/ *$//' | sort > l2

diff l1 l2
