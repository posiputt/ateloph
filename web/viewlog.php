<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<style>body{background:white;}</style>
</head>
<body>
<div style="font-family: monospace; font-size: 14px;">
<?php
	$backgrounds = array(
		0 => '#ffdddd',
		1 => '#ffffff',
	);
	$lines = file($_GET['l']);
	foreach ($lines as $outerkey=>$l) {
		$words = split('[ ]', $l);
		$nick = $words[1];
		$nick = split('[:]',$nick)[0];
		foreach ($words as $key=>$w) {
			if ((stripos($w, 'http') === 0) || (stripos($w, 'ftp') === 0)) {
				if ((stripos($w, '://') > 2) && (stripos($w, '://') < 6)) {
					$words[$key] = '<a href="'.$words[$key].'">' .$words[$key]. '</a>';
				}
			} else {
				$words[$key] = htmlspecialchars($words[$key]);
			}
		};
		$l = implode(' ', $words);
		echo '<div style="margin:0px;color:black;';
		echo 'background:' . $backgrounds[$outerkey%2] . ';';
		echo '">' . $l . '</div>';
	}
	//VAR_DUMP($lines);
?>
</div>
</body>
</html>
