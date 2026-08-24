cmake_minimum_required(VERSION 3.8)
project(coordinacion_msgs)

# El carro real corre Jazzy sobre Ubuntu 24.04 y el PC corre Humble sobre 22.04.
# Este paquete tiene que compilar en los dos, asi que se queda en lo que ambos
# comparten: ament_cmake + rosidl, sin nodos y sin nada especifico de una
# distribucion. Si alguna vez deja de compilar en uno de los dos, el problema
# esta en lo que se acabe de anadir, no en el CMake.

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
# Obligatorio por llevar un .action: rosidl genera goal/result/feedback sobre
# los tipos de action_msgs. Sin esto la generacion falla, no es opcional.
find_package(action_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/EstadoRobot.msg"
  "msg/PuntoInteres.msg"
  "msg/ListaPuntosInteres.msg"
  "msg/EstadoMision.msg"
  "action/GuiarUsuario.action"
  DEPENDENCIES geometry_msgs builtin_interfaces std_msgs action_msgs
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_export_dependencies(rosidl_default_runtime)
ament_package()
