// Copyright 2019 Google LLC & Bastiaan Konings
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// written by bastiaan konings schuiling 2008 - 2015
// this work is public domain. the code is undocumented, scruffy, untested, and should generally not be used for anything important.
// i do not offer support, so don't ask. to be used for inspiration :)

#include "main.hpp"

#include "utils.hpp"

#include "systems/graphics/resources/texture.hpp"
#include <boost/algorithm/string.hpp>
#include <cmath>

float GetQuantizedDirectionBias() {
  DO_VALIDATION;
  return GetConfiguration()->GetReal("gameplay_quantizeddirectionbias", _default_QuantizedDirectionBias);
}

void QuantizeDirection(Vector3 &inputDirection, float bias) {
  DO_VALIDATION;

  // digitize input

  Vector3 inputDirectionNorm = inputDirection.GetNormalized(0);

  int directions = GetConfiguration()->GetInt("gameplay_quantizeddirectioncount", 8);

  radian angle = inputDirectionNorm.GetAngle2D();
  angle /= pi * 2.0f;
  angle = std::round(angle * directions);
  angle /= directions;
  angle *= pi * 2.0f;

  inputDirection = (inputDirectionNorm * (1.0 - bias) + (Vector3(1, 0, 0).GetRotated2D(angle) * bias)).GetNormalized(inputDirectionNorm) * inputDirection.GetLength();
}

Vector3 GetProjectedCoord(const Vector3 &pos3D,
                          boost::intrusive_ptr<Camera> camera) {
  DO_VALIDATION;
  Matrix4 rotMat;
  rotMat.ConstructInverse(camera->GetDerivedPosition(), Vector3(1, 1, 1), camera->GetDerivedRotation());
  float fov = camera->GetFOV();

  // cotangent
  float f = 1.0 / tan((fov / 360.0 * pi * 2) / 2.0);

  Vector3 contextSize3D = GetGraphicsSystem()->GetContextSize();
  float aspect = contextSize3D.coords[0] / contextSize3D.coords[1];
  float aspect2D = GetMenuTask()->GetWindowManager()->GetAspectRatio();
  if (aspect2D < aspect) aspect = aspect2D;

  //printf("aspect: %f\n", aspect);
  float zNear = 40.0;
  float zFar = 270.0;

  Matrix4 perspMat;
  perspMat.elements[0] = f / aspect;
  perspMat.elements[5] = f;
  perspMat.elements[10] = (zFar + zNear) / (zNear - zFar);
  perspMat.elements[11] = (2 * zFar * zNear) / (zNear - zFar);
  perspMat.elements[14] = -1;

  Matrix4 resMat = perspMat * rotMat;

  float x, y, z, w;
  resMat.MultiplyVec4(pos3D.coords[0], pos3D.coords[1], pos3D.coords[2], 1, x, y, z, w);

  Vector3 result;
  result.coords[0] = x / w;
  result.coords[1] = y / w;

  //printf("%f %f %f\n", x / w, y / w, z / w);

  result.coords[1] = -result.coords[1];

  result.coords[1] *= aspect2D / aspect;

  result += 1.0;
  result *= 0.5;
  result *= 100;

  return result;
}

// Construct the transformation matrix from the world to camera coordinates
Matrix4 GetExtrinsicsMatrix(boost::intrusive_ptr<Camera> camera) {
  DO_VALIDATION;
  Matrix3 rotMat;
  Matrix4 resMat;
  Vector3 camPos = camera->GetDerivedPosition();
  // printf("campos: %4.2f, %4.2f, %4.2f \n", camPos.coords[0], camPos.coords[1], camPos.coords[2]);
  Quaternion WorldToCameraRot = camera->GetDerivedRotation();
  WorldToCameraRot.Normalize();
  Quaternion CameraToWorldRot = WorldToCameraRot.GetInverse();
  // printf("camrot: %4.2f, %4.2f, %4.2f, %4.2f\n", WorldToCameraRot.elements[0], WorldToCameraRot.elements[1], WorldToCameraRot.elements[2], WorldToCameraRot.elements[3]);
  CameraToWorldRot.Normalize();
  CameraToWorldRot.ConstructMatrix(rotMat); 
  Vector3 r_cw = rotMat*(-camPos);
  resMat = rotMat;
  resMat.elements[3] = r_cw.coords[0];
  resMat.elements[7] = r_cw.coords[1];
  resMat.elements[11] = r_cw.coords[2];
  return resMat;
} 

Matrix3 GetIntrinsicsMatrix(boost::intrusive_ptr<Camera> camera) {
  float fov = camera->GetFOV();
  Vector3 contextSize3D = GetGraphicsSystem()->GetContextSize();
  float nearCap, farCap;
  float alpha = (contextSize3D.coords[1])/(2*tan((pi/180) * (fov/2))); // Focal length in pixels. FOV IS DEFINED AS THE VERTICAL FIELD OF VIEW!!!!111!!
  float u0 = contextSize3D.coords[0]/2;
  float v0 = contextSize3D.coords[1]/2;
  Matrix3 K;

  K.elements[0] = alpha;
  K.elements[1] = 0;
  K.elements[2] = -u0;
  K.elements[3] = 0;
  K.elements[4] = -alpha; // Flipping y axis format
  K.elements[5] = -v0;
  K.elements[6] = 0;
  K.elements[7] = 0;
  K.elements[8] = -1; // Objects always haved negative z axis
  return K;
}

Vector3 GetPixelCoordinates(const Vector3 &pos3D, boost::intrusive_ptr<Camera> camera) { 
  Matrix4 RT = GetExtrinsicsMatrix(camera);
  Matrix4 K;
  K = GetIntrinsicsMatrix(camera);
  K.elements[3] = 0;
  K.elements[7] = 0;
  K.elements[11] = 0;
  K.elements[12] = 0;
  K.elements[13] = 0;
  K.elements[14] = 0;
  K.elements[15] = 0;
  float xc, yc, zc, wc, xp, yp, zp, w;
  RT.MultiplyVec4(pos3D.coords[0], pos3D.coords[1], pos3D.coords[2], 1, xc, yc, zc, wc);
  K.MultiplyVec4(xc, yc, zc, 0, xp, yp, zp, w);
  int out1 = static_cast<int>(floor(xp/zp)); 
  int out2 = static_cast<int>(floor(yp/zp));
  Vector3 out(out1, out2, 0);
  return out;
}

void processBallOOB(const Vector3 &pos2D, boost::intrusive_ptr<Camera> camera){
  float out1 = pos2D.coords[0];
  float out2 = pos2D.coords[1];
  Vector3 contextSize3D = GetGraphicsSystem()->GetContextSize();
  if (((out1 >= 0) && (out1 <= contextSize3D.coords[0])) && ((out2 >= 0) && (out2 <= contextSize3D.coords[1]))) {
    camera->ballOOB = false;
  } else {
    camera->ballOOB = true;
  }  
}



int GetVelocityID(e_Velocity velo, bool treatDribbleAsWalk) {
  DO_VALIDATION;
  int id = 0;
  switch (velo) {
    DO_VALIDATION;
    case e_Velocity_Idle:
      id = 0;
      break;
    case e_Velocity_Dribble:
      id = 1;
      break;
    case e_Velocity_Walk:
      id = 2;
      break;
    case e_Velocity_Sprint:
      id = 3;
      break;
    default:
      id = 0;
      break;
  }
  if (treatDribbleAsWalk && id > 1) id--;
  return id;
}

std::map < e_PositionName, std::vector<Stat> > defaultProfiles;

float CalculateStat(float baseStat, float profileStat, float age,
                    e_DevelopmentCurveType developmentCurveType) {
  DO_VALIDATION;


  float idealAge = 27;
  float ageFactor = curve( 1.0f - NormalizedClamp(fabs(age - idealAge), 0, 13) * 0.5f , 1.0f) * 2.0f - 1.0f; // 0 .. 1
  assert(ageFactor >= 0.0f && ageFactor <= 1.0f);
  //ageFactor = clamp(ageFactor, 0.0f, 1.0f);

  // this factor should roughly be around 1.0f for good players at their top age.
  float agedBaseStat = baseStat * (ageFactor * 0.5f + 0.5f) * 1.2f;

  float agedProfileStat = clamp(profileStat * 2.0f * agedBaseStat, 0.01f, 1.0f); // profile stat * 2 because average == 0.5

  return agedProfileStat;
}
