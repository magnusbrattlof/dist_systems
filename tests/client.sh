for ((i = 1; i <= 7; i++)); do
	for((j = 1; j <= 2; j++)); do
		curl -d 'entry=m'${j} -X 'POST' 'http://10.1.0.'${i}'/board' &
	done
done