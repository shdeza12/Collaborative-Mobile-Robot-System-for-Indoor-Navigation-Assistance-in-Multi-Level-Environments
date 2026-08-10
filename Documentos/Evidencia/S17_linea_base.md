# Línea base — un robot, antes de aplicar el contrato de interfaces

**Fecha:** 2026-08-05 · **Semana:** S17 · **Hito:** H1

Estado del sistema **antes** de cualquier cambio de namespaces. Sirve como referencia de regresión:
tras aplicar `CONTRATO_INTERFACES.md` §6, un solo robot debe seguir comportándose igual salvo por
el prefijo de namespace y de marcos.

## Cómo se capturó

```
cd ~/deepracer_sim_ws && source install/setup.bash && ros2 launch deepracer_bringup deepracer_sim.launch.py world:=/usr/share/gazebo-11/worlds/empty.world
cd ~/deepracer_sim_ws && source install/setup.bash && cd /tmp && ros2 topic list > base_topics.txt && ros2 control list_controllers > base_ctrl.txt && ros2 run tf2_tools view_frames
```

## Controladores — 7/7 `active`

| Controlador | Tipo | Estado |
|---|---|---|
| `joint_state_broadcaster` | `joint_state_broadcaster/JointStateBroadcaster` | active |
| `left_rear_wheel_velocity_controller` | `velocity_controllers/JointGroupVelocityController` | active |
| `right_rear_wheel_velocity_controller` | `velocity_controllers/JointGroupVelocityController` | active |
| `left_front_wheel_velocity_controller` | `velocity_controllers/JointGroupVelocityController` | active |
| `right_front_wheel_velocity_controller` | `velocity_controllers/JointGroupVelocityController` | active |
| `left_steering_hinge_position_controller` | `position_controllers/JointGroupPositionController` | active |
| `right_steering_hinge_position_controller` | `position_controllers/JointGroupPositionController` | active |

Confirma que la migración Foxy→Humble de S12 (`start` → `active`, `joint_state_controller` →
`joint_state_broadcaster`) sigue vigente.

## Tópicos — 27, todos en la raíz

Del contrato (§2), los que deben quedar bajo `/<ns>`:

```
/cmd_vel   /odom   /scan   /joint_states
/dynamic_joint_states   /robot_description
/<ctrl>/commands   /<ctrl>/transition_event   (×7 controladores)
/zed_camera_left_sensor/camera_info   /zed_camera_left_sensor/image_raw
```

Globales, se quedan donde están: `/clock` `/tf` `/tf_static` `/rosout` `/parameter_events`
`/performance_metrics`.

## Árbol TF — 13 marcos, ninguno prefijado

```
odom                                    <- raíz (publicado por deepracer_drive_plugin, 15,1 Hz)
└── base_link                           <- 19,8 Hz
    └── chassis
        ├── left_steering_hinge  └── left_front_wheel
        ├── right_steering_hinge └── right_front_wheel
        ├── left_rear_wheel
        ├── right_rear_wheel
        ├── zed_camera_link      └── camera_link
        ├── laser
        └── shell
```

No aparece `map` porque este launch no levanta AMCL ni SLAM.
No existe `base_footprint`: el marco base real es `base_link`, coherente con
`deepracer_ros_control.xacro:41` y con los `nav2_params*.yaml`.

**Los 13 nombres son cadenas fijas.** Con un segundo robot, los 13 colisionan.

## Anomalía detectada (preexistente)

`camera_link` aparece con padre `zed_camera_link`, pero
`deepracer_spawn.launch.py:104` publica una transformada estática `base_link` → `camera_link`.

En TF2 un marco solo puede tener **un** padre. Hay dos emisores disputándose `camera_link`:
el URDF y el `static_transform_publisher` del launch. Ambos son estáticos (rate 10000), así que
se sobrescriben mutuamente y el ganador depende del orden de llegada.

No afecta la navegación (Nav2 usa `base_link` y `laser`, no `camera_link`), pero debe resolverse
al tocar el launch para namespaces: con dos robots el conflicto se duplica. Decisión pendiente:
eliminar el `static_transform_publisher` y confiar en el URDF, o al revés.
