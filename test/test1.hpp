/*
 * Copyright (C) 2017 Daniel Mensinger
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#pragma once
#include <string>
#include <vector>

#define HAHA(x)                                                                                                        \
  enum NotPrint { V1 = 2, V4 = 3 };                                                                                    \
  if (true == x) {                                                                                                     \
    return false;                                                                                                      \
  }

using namespace std;

namespace test {

enum [[deprecated("because")]] ENUM1 {
  VAL1, // asdf /* */
      VAL2 /* abc // */, VAL3
};

enum class ENUM2 { AAA = 3, BBB, CCC = AAA, DDD = 4 } asdf;

typedef enum { A, B, C, D } Meh;
typedef enum class Asdf { A, B, C, D } Qwerty;

struct ABC {
  int a;
  int b;
};
struct CDE : ABC {
  int c;
  int d;
};

class AAClass {
  int i;
};

class TestClass final : public AAClass {
  enum PrivateEnum { P_AAA, P_BBB };
  Asdf             aaa;
  Qwerty           bbb;
  Meh              stuff;
  std::vector<int> intVec = {1, 4, 6, 8};
  std::string      str =
      "\
  enum ABC {aad}; \
  String s = \"\" \
  ";

  struct StillPrivate {
    enum OutOfLuck { Meh, No, One, Can, Access, Me, From, The, Outside };
  };

 public:
  enum ABC { WHY, DOES, THIS, CASE, EXIST };
  enum class BLEH : int { THIS, IS, AN, ABSOLUTE, NIGHTMARE };

  TestClass() = default;
  TestClass(int a, int c = 0) : aaa(Asdf::A) {
    (void)a;
    (void)c;
    if (a == 0) {
      bbb = Asdf::B;
    }
  }

  void doStuffenum() noexcept;
  int  enumReturnStuff() const;

 private:
  enum AnotherPrivateEnum { P_CCC, P_DDD };
};

void TestClass::doStuffenum() noexcept { stuff = B; }

int TestClass::enumReturnStuff() const { return 0; }



template <class T>
class Templates {
  template <class A>
  void f(A a, T t);
};

template <class T>
template <class A>
void Templates<T>::f(A a, T t) {
  (void)a;
  (void)t;
}



} // namespace test
