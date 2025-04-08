<?php
require_once 'ZKLibrary.php';

$zk = new ZKLibrary('192.168.2.107', 4370); // Cambia la IP por la de tu reloj
$zk->connect();
$zk->disableDevice();

// Conexión a la base de datos SQLite
$db = new SQLite3('/ruta/completa/a/tu/proyecto/db.sqlite3');

// --- 1. Guardar/Actualizar usuarios ---
$usuarios = $zk->getUser();

foreach ($usuarios as $u) {
    $uid = $u[0];
    $user_id = $u[1];
    $nombre = $u[2];
    $privilegio = $u[3];
    $password = $u[4];
    $grupo = $u[5];
    $enabled = $u[6];

    // Verificar si el usuario ya existe
    $check = $db->querySingle("SELECT COUNT(*) as count FROM gestion_visitantes_usuarioreloj WHERE user_id = '$user_id'");

    if ($check > 0) {
        // Update
        $stmt = $db->prepare("UPDATE gestion_visitantes_usuarioreloj 
            SET uid=:uid, nombre=:nombre, privilegio=:privilegio, password=:password, grupo=:grupo, enabled=:enabled 
            WHERE user_id=:user_id");
    } else {
        // Insert
        $stmt = $db->prepare("INSERT INTO gestion_visitantes_usuarioreloj 
            (uid, user_id, nombre, privilegio, password, grupo, enabled) 
            VALUES (:uid, :user_id, :nombre, :privilegio, :password, :grupo, :enabled)");
    }

    $stmt->bindValue(':uid', $uid, SQLITE3_INTEGER);
    $stmt->bindValue(':user_id', $user_id, SQLITE3_TEXT);
    $stmt->bindValue(':nombre', $nombre, SQLITE3_TEXT);
    $stmt->bindValue(':privilegio', $privilegio, SQLITE3_INTEGER);
    $stmt->bindValue(':password', $password, SQLITE3_TEXT);
    $stmt->bindValue(':grupo', $grupo, SQLITE3_INTEGER);
    $stmt->bindValue(':enabled', $enabled, SQLITE3_INTEGER);
    $stmt->execute();
}

// --- 2. Guardar registros de asistencia ---
$asistencias = $zk->getAttendance();

foreach ($asistencias as $a) {
    $codigo = $a[1];
    $fecha = $a[3];
    $tipo = $a[2] == 0 ? 'Entrada' : 'Salida';

    // Insertar registro
    $stmt = $db->prepare("INSERT INTO gestion_visitantes_registroasistencia 
        (usuario_id, fecha_hora, tipo_evento) 
        VALUES (:usuario, :fecha, :tipo)");

    $stmt->bindValue(':usuario', $codigo, SQLITE3_TEXT); // user_id como clave foránea
    $stmt->bindValue(':fecha', $fecha, SQLITE3_TEXT);
    $stmt->bindValue(':tipo', $tipo, SQLITE3_TEXT);
    $stmt->execute();
}

$zk->enableDevice();
$zk->disconnect();

echo "✅ Usuarios y registros de asistencia importados correctamente.\n";
?>