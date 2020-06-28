for i in `cat data-list.txt `;
do
	echo "Replace: "$i
	sed -i.bak "s/__DATA__/sub data\{\nmy \$data=\<\<\'HTML\'\;/g" $i
	echo "Backup: "$i.bak
	sed -i "s/my \$html = <DATA>/my \$html = data()/g" $i
	sed -i -e "\$aHTML\nreturn \$data;\}" $i
done
